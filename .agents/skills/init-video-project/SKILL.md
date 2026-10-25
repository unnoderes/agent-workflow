---
name: init-video-project
description: 初始化视频制作项目目录。当用户提到新视频主题、或即将调用任何视频生产技能（short-video-frames / short-video-cover / tts-video）时，自动将 Desktop 上的 directory-template 副本复制到用户指定的位置，并按视频主题重命名。
allowed-tools: [AskUserQuestion, Bash, Read]
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

### Step 0 — 确认项目创建位置

**使用 AskUserQuestion 工具询问项目创建位置**：

```json
{
  "questions": [
    {
      "question": "请选择项目创建位置：",
      "header": "创建位置",
      "multiSelect": false,
      "options": [
        {
          "label": "桌面（默认）",
          "description": "~/Desktop — 便于快速访问和文件管理"
        },
        {
          "label": "当前目录",
          "description": ". — 在当前工作目录下创建"
        },
        {
          "label": "文档目录",
          "description": "~/Documents — 与其他文档一起归档"
        }
      ]
    }
  ]
}
```

**选项处理逻辑**：

- 选择“桌面（默认）” → 使用 `~/Desktop` 或 `C:/Users/Administrator/Desktop`
- 选择“当前目录” → 使用 `.`（当前工作目录）
- 选择“文档目录” → 使用 `~/Documents` 或 `C:/Users/Administrator/Documents`
- 选择“Other”（自定义输入） → 使用用户提供的路径（需验证目录存在）

**路径验证**：

在使用用户选择的目录前，必须验证其存在：

```bash
# 验证目录存在
if [ ! -d "<用户选择的路径>" ]; then
    echo "错误：目录 <用户选择的路径> 不存在"
    exit 1
fi
```

或 PowerShell：

```powershell
if (-not (Test-Path "<用户选择的路径>")) {
    Write-Error "错误：目录 <用户选择的路径> 不存在"
    exit 1
}
```

如果用户选择的目录不存在，向用户报告错误并要求重新选择。

---

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

**步骤 2.3**：复制模板目录到用户指定的项目位置

执行复制（bash）：
```bash
cp -r "C:/Users/Administrator/Desktop/directory-template" "<用户选择的路径>/<项目目录名>"
```

或 PowerShell：
```powershell
Copy-Item -Path "C:\Users\Administrator\Desktop\directory-template" `
          -Destination "<用户选择的路径>\<项目目录名>" -Recurse
```

**重要**：
- 如果用户选择了“当前目录”，使用 `./<项目目录名>`
- 如果选择了“桌面”，使用 `~/Desktop/<项目目录名>` 或 `C:/Users/Administrator/Desktop/<项目目录名>`
- 如果选择了“文档目录”，使用 `~/Documents/<项目目录名>` 或 `C:/Users/Administrator/Documents/<项目目录名>`

复制完成后验证目录存在，不存在则报错停止。

---

### Step 3 — 输出初始化摘要

```
已初始化项目目录：<用户选择的路径>/<项目目录名>/

  html/              HTML 预览文件（frames + cover 的源文件）
  画面/              导出的画面帧 PNG
  封面/              导出的封面 PNG
  音频/              TTS 音频（final.mp3 + segments/）
  字幕/              SRT 字幕文件

后续所有技能的输出请写入上述对应子目录（见下方「项目目录结构」）。
```

**注意**：
- 如果用户选择了“当前目录”，显示为 `./<项目目录名>/`
- 如果选择了“桌面”，显示为 `~/Desktop/<项目目录名>/`
- 如果选择了“文档目录”，显示为 `~/Documents/<项目目录名>/`
- 如果是自定义路径，显示完整路径

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

- **项目创建位置**：默认为桌面目录，但用户可以选择当前目录、文档目录或自定义路径。
- **模板目录自动创建**：如果 Desktop 上没有 `directory-template` 目录，会自动创建标准结构。
- **模板目录为只读参照**：始终复制，不得直接修改 Desktop 上的原始目录。
- **每个视频独立目录**：每个视频主题对应一个独立的项目目录，不要在同一目录下混放多个视频的文件。
- **技能不随项目复制**：所有技能始终从本仓库 `.agents/skills/` 加载，不复制进每个视频项目目录。
- **后续 skill 应使用用户选择的路径**：所有后续的视频生产 skills（short-video-frames / tts-video 等）都应将文件写入用户选择的项目目录，不是固定的桌面目录。
