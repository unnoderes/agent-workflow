# Notion-Based Video Production Workflow

这是一个基于 Notion 的两阶段视频制作工作流，将素材收集和脚本生成分离，支持团队协作和内容复用。

## 核心优势

- **职责分离**：素材收集与脚本生成独立，各司其职
- **中间可审核**：人工可在 Notion 中补充/删减素材
- **可复用**：一份素材库可生成多种风格的脚本
- **团队协作**：多人可同时在 Notion 编辑素材
- **可追溯**：所有中间产物永久保存在 Notion

## 两阶段流程

### Phase 1: 素材收集 (`collect-video-materials`)

**输入**：视频主题  
**输出**：Notion 工作空间（包含素材库和脚本占位页面）

**执行步骤**：
1. 创建 Notion 工作空间（工作区主页 + 素材库 + 脚本占位）
2. 联网搜索 3+ 次（核心信息、案例、痛点）
3. 提取结构化素材（钩子、数据、案例、对比）
4. 写入 Notion 素材库页面
5. 返回工作空间 URL

**命令示例**：
```bash
"Collect materials for video: React Server Components 入门教程"
```

**Notion 工作空间结构**：
```
🎬 [主题] - 视频制作工作区
  ├─ 📋 项目信息
  ├─ 📚 素材库（子页面）
  │   ├─ 🎣 钩子素材
  │   ├─ 📊 数据素材
  │   ├─ 💡 案例素材
  │   ├─ 🔄 对比素材
  │   └─ 🔗 参考链接
  └─ 📝 视频脚本（子页面，待生成）
```

---

### Phase 2: 脚本生成 (`generate-video-script`)

**输入**：Notion 工作空间 URL（Phase 1 输出）  
**输出**：完整视频脚本（写入 Notion）

**执行步骤**：
1. 读取 Notion 素材库内容
2. 分析素材覆盖度（钩子、数据、案例、对比）
3. 按需补充搜索（0-3 次，仅补充缺失部分）
4. 设计视频结构（根据时长和主题）
5. 生成分段脚本（文案、视觉、关键词、节奏）
6. 推荐制作参数（比例、风格、TTS）
7. 写回 Notion 脚本页面
8. 返回脚本页面 URL

**命令示例**：
```bash
"Generate script from workspace: https://notion.so/xxx-xxx"
```

**脚本页面结构**：
```
📝 视频脚本
  ├─ 内容结构（总时长、段落划分）
  ├─ 分段脚本
  │   ├─ 第 1 段（文案 + 视觉 + 关键词 + 节奏）
  │   ├─ 第 2 段 ...
  │   └─ 第 N 段 ...
  ├─ 制作参数建议
  │   ├─ 画面比例（9:16 / 16:9 / 1:1）
  │   ├─ 美术风格（5 种预设）
  │   └─ TTS 配置（音色 + 语速）
  ├─ 素材使用情况
  └─ 下一步行动（checklist）
```

---

## 完整工作流示例

### 1. 收集素材

```bash
# AI 执行
"Collect materials for video: React Server Components 实战入门"

# 输出
✅ 素材收集完成！

📦 Notion 工作区: https://notion.so/React-Server-Components-xxx

📊 收集统计:
  - 钩子素材: 3 个
  - 数据素材: 4 个
  - 案例素材: 2 个
  - 对比素材: 1 个
  - 参考链接: 5 个

🚀 下一步:
运行 `generate-video-script` 并提供工作区 URL，生成视频脚本。
```

### 2. 人工审核（可选）

在 Notion 中打开工作区，审核素材库内容：
- 补充遗漏的素材
- 删除不相关的素材
- 调整素材的优先级
- 添加团队成员协作编辑

### 3. 生成脚本

```bash
# AI 执行
"Generate script from workspace: https://notion.so/React-Server-Components-xxx"

# 输出
✅ 视频脚本生成完成！

📝 Notion 脚本页面: https://notion.so/Video-Script-xxx

📊 脚本统计:
  - 总时长: 60 秒
  - 脚本段数: 5 段
  - 素材使用:
    · 钩子: 1 个
    · 数据: 3 个
    · 案例: 2 个
    · 对比: 1 个
  - 补充搜索: 0 次（素材充分）

🎨 制作参数建议:
  - 画面比例: 9:16（抖音竖屏）
  - 美术风格: 2 · 暗色技术感
  - TTS 音色: Chinese_deep_voiced_male_vv1
  - TTS 语速: 1.2

🎬 Notion 工作区: https://notion.so/React-Server-Components-xxx

🚀 下一步:
1. 运行 `init-video-project` 初始化本地项目目录
2. 将脚本内容传递给后续制作 skills
```

### 4. 本地制作

```bash
# 初始化项目目录
"Run init-video-project for RSC实战入门"

# 生成画面、封面、音频（可并行）
"Generate frames from the Notion script"
"Generate cover from the Notion script"
"Generate audio from the Notion script"

# 导出 PNG
"Export HTML to PNG"

# 合成最终视频
"Assemble the final video"
```

---

## 进阶用法

### 一份素材生成多个版本

```bash
# Phase 1: 收集素材（一次）
"Collect materials for video: TypeScript 类型系统"

# Phase 2a: 生成快节奏版本（30 秒，抖音）
"Generate 30-second script from workspace [URL], optimized for TikTok"

# Phase 2b: 生成深度教程版本（120 秒，B站）
"Generate 120-second educational script from workspace [URL], optimized for Bilibili"
```

### 团队协作流程

1. **内容策划**运行 Phase 1，创建素材库
2. **领域专家**在 Notion 补充专业素材和数据
3. **文案编辑**运行 Phase 2，生成脚本初稿
4. **视频制作**审核脚本后执行本地制作流程

### 批量生产

```bash
# 预先收集多个主题的素材
"Collect materials for video: React Hooks"
"Collect materials for video: Next.js App Router"
"Collect materials for video: Tailwind CSS"

# 统一生成脚本（可自动化）
"Generate script from workspace [URL1]"
"Generate script from workspace [URL2]"
"Generate script from workspace [URL3]"
```

---

## 素材库最佳实践

### 钩子素材

好的钩子示例：
- **数据型**：「90% 的开发者都不知道这个技巧」
- **疑问型**：「为什么 React 要推出 Server Components？」
- **反差型**：「你以为的 SSR，其实不是 SSR」

### 数据素材

好的数据示例：
- 具体数值：「首屏加载减少 40%」
- 对比数据：「从 3s 降到 1.2s」
- 权威来源：「React 官方团队测试数据」

### 案例素材

好的案例示例：
- 真实场景：「Vercel Dashboard 的实际应用」
- 具体效果：「将 Bundle 体积从 500KB 减少到 50KB」
- 可复现：「你也可以在自己项目中这样做」

---

## 故障排查

### Notion MCP 连接失败

```bash
# 检查 MCP 连接状态
"List available MCP servers"

# 重新连接 Notion
"Reconnect Notion MCP server"
```

### 素材覆盖度不足

Phase 2 会自动检测并补充搜索，但如果仍不满意：
```bash
# 返回 Phase 1，手动补充素材
"Add more case studies to the materials library at [Notion URL]"
```

### 脚本风格不符合预期

```bash
# 在 Notion 中编辑脚本页面，或重新生成
"Regenerate script from workspace [URL] with [具体要求]"
```

---

## 与旧版 `video-script-planning` 的对比

| 特性 | 旧版（单阶段） | 新版（两阶段） |
|------|-------------|-------------|
| 素材管理 | 临时文本 | Notion 永久保存 |
| 中间审核 | 不支持 | 支持人工介入 |
| 内容复用 | 不支持 | 一份素材多版本脚本 |
| 团队协作 | 不支持 | Notion 多人编辑 |
| 流程灵活性 | 一次性执行 | 分阶段可控 |
| 搜索效率 | 固定 3+ 次 | 智能补充 0-3 次 |

---

## 参考文档

- [collect-video-materials SKILL.md](.agents/skills/collect-video-materials/SKILL.md)
- [generate-video-script SKILL.md](.agents/skills/generate-video-script/SKILL.md)
- [agents.md](agents.md) - 完整流水线说明
- [README.md](README.md) - 项目总览
