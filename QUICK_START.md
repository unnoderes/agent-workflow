# Quick Start: Notion-Based Video Production

## 🚀 完整流程（3分钟上手）

### Step 1: 收集素材（~2分钟）
```bash
"Collect materials for video: React Server Components 入门"
```
**输出**: Notion 工作空间 URL

### Step 2: 生成脚本（~1分钟）
```bash
"Generate script from workspace: [上一步的 Notion URL]"
```
**输出**: 完整视频脚本（已写入 Notion）

### Step 3: 本地制作（使用现有 skills）
```bash
"Run init-video-project for RSC入门"
"Generate frames, cover, and audio from the Notion script"
"Export HTML to PNG and assemble the final video"
```

---

## 📋 技能速查

| Skill | 输入 | 输出 | 时间 |
|-------|------|------|------|
| `collect-video-materials` | 视频主题 | Notion 工作空间 | ~2分钟 |
| `generate-video-script` | Notion 工作空间 URL | Notion 脚本页面 | ~1分钟 |
| `init-video-project` | 项目名称 | 本地项目目录 | 秒级 |
| `short-video-frames` | 脚本内容 | HTML 画面文件 | ~1分钟 |
| `short-video-cover` | 视频标题 | HTML 封面文件 | 秒级 |
| `tts-video` | 文案内容 | MP3 + SRT | ~30秒 |
| `html-image-export` | HTML 文件 | PNG 图片 | ~10秒 |
| `assemble-video` | PNG + MP3 + SRT | 最终 MP4 | ~20秒 |

---

## 🎯 常见场景

### 场景 1: 标准单个视频制作
```bash
# 1. 收集素材
"Collect materials for video: [主题]"

# 2. 生成脚本
"Generate script from workspace: [URL]"

# 3. 本地制作
"Init project, generate all assets, and assemble video"
```

### 场景 2: 一份素材多个版本
```bash
# 1. 收集素材（一次）
"Collect materials for video: TypeScript 类型系统"

# 2a. 快节奏版本（30秒，抖音）
"Generate 30-second TikTok script from workspace: [URL]"

# 2b. 深度教程版本（120秒，B站）
"Generate 120-second educational script from workspace: [URL]"
```

### 场景 3: 团队协作
```bash
# 内容策划执行 Phase 1
"Collect materials for video: [主题]"

# → 领域专家在 Notion 补充专业素材

# 文案编辑执行 Phase 2
"Generate script from workspace: [URL]"

# → 视频制作执行本地流程
```

---

## 🔧 必需的 MCP 工具调用

### collect-video-materials 使用的工具
- `web_search`: 联网搜索素材（3+ 次）
- `notion__notion_create_pages__22d0df52`: 创建 Notion 页面
- `notion__notion_update_page__2109c370`: 更新 Notion 内容

### generate-video-script 使用的工具
- `notion__notion_fetch__ce83b000`: 读取 Notion 内容
- `notion__notion_update_page__2109c370`: 写回脚本内容
- `web_search`: 按需补充搜索（0-3 次）

---

## 💡 实用技巧

### 提高素材质量
- 搜索时加上 "2025" 或 "最新" 关键词
- 提供具体的应用场景而非泛泛的概念
- 明确目标受众（开发者、产品经理、初学者等）

### 优化脚本效果
- Phase 1 完成后在 Notion 手动补充关键案例
- 删除过时或不相关的素材
- 标注素材优先级（哪些是核心卖点）

### 加速制作流程
- 使用 Notion 模板预设常用素材分类
- 建立素材复用库（经典钩子、通用数据）
- 批量收集多个主题素材，统一生成脚本

---

## 📚 详细文档

- **完整工作流指南**: [NOTION_WORKFLOW.md](NOTION_WORKFLOW.md)
- **Skill 详细文档**: 
  - [collect-video-materials](.agents/skills/collect-video-materials/SKILL.md)
  - [generate-video-script](.agents/skills/generate-video-script/SKILL.md)
- **项目总览**: [README.md](README.md)
- **流水线说明**: [agents.md](agents.md)
