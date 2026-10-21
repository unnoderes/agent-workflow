---
name: tts-video
description: 根据分段式视频文案调用 MiniMax TTS 生成音频文件并制作 SRT 字幕。用户提供文案后询问音色和语速，批量生成各段 mp3 并合并，输出完整 SRT。触发词：视频配音、TTS生成、文案转语音、生成字幕。
user-invocable: true
tools: Read, Write, Bash
---

# /tts-video — 视频文案转语音 + 字幕

Arguments: `$ARGUMENTS`

---

## 流程

### 第一步：获取文案

如果 `$ARGUMENTS` 不为空，将其作为文案内容。否则请用户粘贴分段文案，格式说明：

> 每段之间用空行分隔，或用数字序号（1. 2. 3.）开头均可。

### 第二步：确认参数（一次性询问，不要分开问）

向用户展示以下问题，等待一次回复：

```
请确认以下参数：

1. 音色 voice_id（默认：Chinese_deep_voiced_male_vv1）
   常用中文男声参考：
   - Chinese_deep_voiced_male_vv1    浑厚男声
   - Chinese (Mandarin)_Radio_Host   电台男主播
   - Chinese (Mandarin)_Reliable_Executive  沉稳高管
   - male-qn-jingying                精英青年
   直接回车使用默认，或输入其他 voice_id。

2. 语速 speed（默认：1.2，范围 0.5~2.0）

3. 输出目录（默认：~/tts_output）
```

### 第三步：解析文案为段落列表

用 Python 解析用户文案，规则：
- 按空行分段；或匹配 `^\d+[.、]\s*` 前缀后去除序号
- 过滤空段
- 打印解析结果让用户确认段数

### 第四步：试听确认（可选）

用第一段文案调用 TTS，保存为 `{output_dir}/preview.mp3`，告知用户路径：

```
预览文件：{output_dir}/preview.mp3
可用以下命令播放：
  macOS：afplay {output_dir}/preview.mp3
  Linux：mpv {output_dir}/preview.mp3  或  aplay
  Windows：start {output_dir}/preview.mp3

回复 y 继续批量生成，或 n 取消。默认 30 秒内无回复视为 y。
```

### 第五步：批量生成音频

对每段依次调用 MiniMax TTS API：

```bash
curl -s -X POST "https://api.minimax.chat/v1/t2a_v2" \
  -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "speech-02-turbo",
    "text": "<段落文本>",
    "stream": false,
    "voice_setting": {"voice_id": "<voice_id>", "speed": <speed>, "vol": 1.0, "pitch": 0},
    "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"}
  }'
```

- 保存为 `{output_dir}/segments/seg_001.mp3`、`seg_002.mp3` 等
- 每段完成后用 Python `mutagen.mp3.MP3` 读取时长（如无 mutagen，用 ffprobe），累计时间轴
- 实时打印进度：`[2/5] 生成中...`

### 第六步：生成 SRT 字幕

用 Python 生成，段间插入 300ms 间隔：

```python
def ms_to_srt_time(ms):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# 对每段：
# start = 上一段结束时间 + 300ms（第一段从 0 开始）
# end   = start + 本段音频时长
```

输出到 `{output_dir}/subtitles.srt`。

### 第七步：合并音频

用 ffmpeg 拼接所有 segments（段间插入 300ms 静音）：

```bash
# 生成 concat list
python3 -c "
import os
segs = sorted([f for f in os.listdir('{output_dir}/segments') if f.endswith('.mp3')])
with open('{output_dir}/concat.txt', 'w') as f:
    for i, s in enumerate(segs):
        f.write(f\"file 'segments/{s}'\n\")
        if i < len(segs)-1:
            f.write(\"file 'silence.mp3'\n\")
"
# 先生成 300ms 静音
ffmpeg -f lavfi -i anullsrc=r=32000:cl=mono -t 0.3 -q:a 9 -acodec libmp3lame {output_dir}/silence.mp3 -y -loglevel error
# 合并
ffmpeg -f concat -safe 0 -i {output_dir}/concat.txt -acodec copy {output_dir}/final.mp3 -y -loglevel error
```

### 第八步：输出摘要

```
完成！
  segments/   各段 mp3（共 N 段）
  final.mp3   合并音频
  subtitles.srt  SRT 字幕

总时长：X 秒
输出目录：{output_dir}
```

---

## 错误处理

- API 返回非 0 状态码：打印错误信息，跳过该段并继续，最后汇报哪些段失败
- mutagen 未安装：改用 `ffprobe -v error -show_entries format=duration -of csv=p=0 file.mp3`
- ffmpeg 未安装：跳过合并步骤，告知用户只输出了分段文件
