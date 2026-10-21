---
name: assemble-video
description: 将 PNG 帧序列 + MP3 音频 + SRT 字幕拼接为最终 MP4，无需剪辑软件。按 SRT 时间戳决定每帧停留时长，支持硬字幕烧录、软字幕封装或无字幕。触发词：视频拼接、合成视频、导出 MP4、FFmpeg 出片。
user-invocable: true
tools: Read, Write, Bash
---

# /assemble-video — PNG + MP3 + SRT → MP4

Arguments: `$ARGUMENTS`

流水线的最后一步。把 `html-image-export` 导出的画面帧、`tts-video` 生成的音频和字幕合成成品视频，不经过剪映 / Premiere。

---

## 流程

### 第一步：确认项目目录

项目目录应包含（由 `init-video-project` 创建）：

```
<项目目录>/
  画面/frame_01.png … frame_N.png   ← html-image-export
  音频/final.mp3                   ← tts-video
  字幕/subtitles.srt               ← tts-video
```

如果 `$ARGUMENTS` 指定了目录，直接使用；否则询问用户项目目录路径。

### 第二步：确认参数（一次性询问，不要分开问）

```
请确认以下参数：

1. 字幕模式
   A · 硬字幕烧录（默认）— 烧进画面，微信视频号 / 小红书等平台都支持
   B · 软字幕封装 — 播放器里可关闭，但部分平台不显示
   C · 无字幕

2. 输出文件名（默认：final_output.mp4）

3. 硬字幕字号（默认：24，白字黑描边 2px）
```

### 第三步：检查依赖

脚本会自动完成，无需手动执行。它会确认：

- `ffmpeg` / `ffprobe` 是否安装（缺失时给出各平台安装命令）
- `画面/` `音频/final.mp3` `字幕/subtitles.srt` 是否存在
- PNG 帧数是否等于 SRT 段数（一帧对一段，不匹配直接报错）
- 所有帧尺寸是否一致、宽高是否为偶数（H.264 的 `yuv420p` 要求）
- 字幕是否为 UTF-8

想先看一遍将要执行的命令，加 `--dry-run`。

### 第四步：执行拼接

```bash
python scripts/assemble_video.py "<项目目录>" --subtitles hard
```

脚本会解析 SRT 时间戳 → 生成 `concat_list.txt` → 执行一次 FFmpeg 编码 → 用 ffprobe 复核输出。

实时进度：

```
[INFO] 检查依赖…
[OK] FFmpeg 已安装：/usr/local/bin/ffmpeg
[OK] 找到 12 个 PNG 帧
[OK] 画面尺寸 1920x1080，全部帧一致
[OK] 音频文件存在（45.30s）
[OK] 字幕文件存在（12 段）
[OK] concat 清单：concat_list.txt，总时长 45.300s
[INFO] 执行 FFmpeg 拼接…
[INFO] 编码进度：40% (18.1s / 45.3s)
[INFO] 编码进度：80% (36.2s / 45.3s)
```

### 第五步：输出摘要

```
[SUCCESS] 视频生成完成！
- 路径：<项目目录>/final_output.mp4
- 大小：12.5 MB
- 时长：00:00:45.30
- 分辨率：1920x1080
- 编码：H264 + AAC
- 字幕：硬字幕烧录

[INFO] 预览命令：
  ffplay "<项目目录>/final_output.mp4"
```

把摘要转述给用户，并提示可上传到目标平台。

---

## 参数速查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--subtitles` | `hard` | `hard` 烧录 / `soft` 封装 / `none` 无字幕 |
| `--output` | `final_output.mp4` | 输出文件（相对项目目录） |
| `--font-size` | `24` | 硬字幕字号 |
| `--force-style` | — | 覆盖完整 ASS 样式串，用于自定义字体/颜色/位置 |
| `--fps` | `30` | 输出帧率，决定字幕对齐精度（1/30s ≈ 33ms） |
| `--crf` | `23` | x264 质量，越小越清晰、文件越大（18–28） |
| `--preset` | `medium` | x264 编码速度 |
| `--audio-bitrate` | `192k` | AAC 码率 |
| `--frames-dir` / `--audio` / `--srt` | 见上 | 非标准目录结构时覆盖输入路径 |
| `--manifest` | `concat_list.txt` | concat 清单路径 |
| `--force` | 关 | 允许覆盖已存在的输出文件 |
| `--dry-run` | 关 | 只检查输入并打印 FFmpeg 命令 |

单独解析时间轴（调试用）：

```bash
python scripts/parse_srt_durations.py "<项目目录>/字幕/subtitles.srt"
python scripts/generate_concat_list.py "<项目目录>/字幕/subtitles.srt" "<项目目录>/画面" "<项目目录>/concat_list.txt" --pad-to 45.3
```

---

## 时间轴规则

- **一帧对一段字幕**：第 N 段字幕的时长就是第 N 帧的停留时长。帧数与段数不一致时报错，不猜测。
- **画面切换按 SRT 时间戳**：`fps=30:round=down` 保证切换发生在字幕开始的那一刻，误差 < 1 帧（33ms），实测为 0。
- **字幕比音频短**：延长最后一帧补满音频时长，并给出 `[WARN]`。
- **字幕比音频长**：输出会被 `-shortest` 裁到音频长度，同样给出 `[WARN]`，提示检查字幕时间轴。
- 字幕段落时间重叠时会给出 `[WARN]`，但仍按顺序拼接。

---

## 错误处理

| 情况 | 行为 |
|------|------|
| `ffmpeg` 未安装 | 打印 Windows / macOS / Linux 安装命令后退出 |
| 缺少 `final.mp3` 或 `subtitles.srt` | 提示先运行 `tts-video` |
| 缺少 PNG 帧 | 提示先运行 `html-image-export` |
| 帧数 ≠ 字幕段数 | 列出两边数量，不强行拼接 |
| 帧尺寸不一致 / 宽高为奇数 | 列出每种尺寸的帧数，或说明需要偶数像素 |
| SRT 非 UTF-8 或格式错误 | 报出出错行号，UTF-8 问题附 `iconv` 转换命令 |
| PNG 带透明通道 | 警告透明区域会变黑（H.264 无 alpha） |
| 输出文件已存在 | 拒绝覆盖，提示加 `--force` 或改 `--output` |
| FFmpeg 编码失败 | 打印 FFmpeg 的 stderr 原文 |

所有错误都以 `[ERROR]` 开头、退出码 1，且不留下半成品输出（输出文件写入失败时不会残留可播放的残缺 MP4）。

---

## 注意

- 输出为 H.264 + AAC 192kbps + `yuv420p`，兼容所有主流平台。
- `concat_list.txt` 是中间产物，可以删除；路径相对于清单所在目录，项目目录整体移动后重新生成即可。
- 一帧对一段字幕是硬性规则：如果某段字幕需要多帧表达，请在 `short-video-frames` 阶段拆分文案，而不是在这里合并。
- 硬字幕默认白字黑边。需要自定义字体时用 `--force-style` 传完整 ASS 样式串。
