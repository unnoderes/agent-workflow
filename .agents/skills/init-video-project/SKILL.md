---
name: init-video-project
description: 初始化视频制作项目目录。当用户提到新视频主题、或即将调用任何视频生产技能（short-video-frames / short-video-cover / tts-video）时，自动将 Desktop 上的 directory-template 副本复制到当前项目根目录，并按视频主题重命名。
---

# init-video-project

## 触发条件

满足以下任一条件时，在其他视频技能执行前优先运行本技能：

- 用户提及新视频的主题、标题或选题
- 即将首次调用 `short-video-frames`、`short-video-cover`、`tts-video` 中的任意一个
- 当前工作目录下不存在已匹配当前视频主题的项目目录

如果目标目录已存在，**停止并询问用户**，不要静默覆盖。

---

## 工作流

### Step 1 — 推导项目目录名

从视频主题推导一个简短的目录名，规则：

- 长度：中文 2–6 字，英文 2–5 个单词（用 `-` 连接）
- 字符：仅允许中文字符、字母、数字、`-`、`_`
- 不加空格、不加括号、不加标点
- 无法推导时（主题未明确），询问用户一句话描述再继续

命名示例：

| 视频主题 | 目录名 |
|----------|--------|
| 介绍 React Hooks 的用法 | `react-hooks入门` |
| Git 工作流最佳实践 | `git工作流教程` |
| Cursor AI 编辑器评测 | `cursor-ai评测` |

---

### Step 2 — 检查并准备模板目录

**步骤 2.1**：检查模板目录是否存在

模板固定路径（本机）：
```
C:\Users\Administrator\Desktop\directory-template
```

检查命令（bash）：
```bash
if [ ! -d "C:/Users/Administrator/Desktop/directory-template" ]; then
    echo "模板目录不存在"
fi
```

或 PowerShell：
```powershell
Test-Path "C:\Users\Administrator\Desktop\directory-template"
```

**步骤 2.2**：如果模板目录不存在，自动创建标准结构

当检测到模板目录不存在时，**不要报错停止**，而是自动创建标准目录结构：

```bash
mkdir -p "C:/Users/Administrator/Desktop/directory-template/html"
mkdir -p "C:/Users/Administrator/Desktop/directory-template/画面"
mkdir -p "C:/Users/Administrator/Desktop/directory-template/封面"
mkdir -p "C:/Users/Administrator/Desktop/directory-template/音频"
mkdir -p "C:/Users/Administrator/Desktop/directory-template/字幕"
```

或 PowerShell：
```powershell
$templatePath = "C:\Users\Administrator\Desktop\directory-template"
New-Item -Path "$templatePath\html" -ItemType Directory -Force
New-Item -Path "$templatePath\画面" -ItemType Directory -Force
New-Item -Path "$templatePath\封面" -ItemType Directory -Force
New-Item -Path "$templatePath\音频" -ItemType Directory -Force
New-Item -Path "$templatePath\字幕" -ItemType Directory -Force
```

创建完成后向用户说明：
```
ℹ️ 检测到 Desktop 上没有 directory-template 模板目录。
已自动创建标准目录结构：
  C:\Users\Administrator\Desktop\directory-template\
    ├── html/
    ├── 画面/
    ├── 封面/
    ├── 音频/
    └── 字幕/

此模板将用于后续所有视频项目的初始化。
```

**步骤 2.3**：复制模板目录到项目位置

执行复制（bash）：
```bash
cp -r "C:/Users/Administrator/Desktop/directory-template" "./<项目目录名>"
```

或 PowerShell：
```powershell
Copy-Item -Path "C:\Users\Administrator\Desktop\directory-template" `
          -Destination ".\<项目目录名>" -Recurse
```

复制完成后验证目录存在，不存在则报错停止。

---

### Step 3 — 输出初始化摘要

```
已初始化项目目录：./<项目目录名>/

  html/              HTML 预览文件（frames + cover 的源文件）
  画面/              导出的画面帧 PNG
  封面/              导出的封面 PNG
  音频/              TTS 音频（final.mp3 + segments/）
  字幕/              SRT 字幕文件

后续所有技能的输出请写入上述对应子目录（见下方「项目目录结构」）。
```

---

## 项目目录结构

这是本流水线唯一的输出布局。后续每个技能只往对应子目录写，不再各自协商路径。

```
<项目目录名>/
  html/                               HTML 源文件
    frame_01.html … frame_N.html      ← short-video-frames
    cover.html                        ← short-video-cover
  画面/                               导出的画面帧      ← html-image-export
    frame_01.png … frame_N.png
  封面/                               导出的封面        ← html-image-export
    cover.png
  音频/                               TTS 音频          ← tts-video
    final.mp3
    segments/seg_001.mp3 …
  字幕/                               SRT 字幕          ← tts-video
    subtitles.srt
  final_output.mp4                    ← assemble-video
  concat_list.txt                     ← assemble-video（中间产物，可删除）
```

`assemble_video.py` 把 `画面/`、`音频/final.mp3`、`字幕/subtitles.srt` 写死在 `PROJECT_DIRS` 里，这就是这个布局不能改的原因。

---

## 注意

- **模板目录自动创建**：如果 Desktop 上没有 `directory-template` 目录，会自动创建标准结构。
- **模板目录为只读参照**：始终复制，不得直接修改 Desktop 上的原始目录。
- **每个视频独立目录**：每个视频主题对应一个独立的项目目录，不要在同一目录下混放多个视频的文件。
- **技能不随项目复制**：所有技能始终从本仓库 `.agents/skills/` 加载，不复制进每个视频项目目录。
