---
name: short-video-cover
description: 为短视频生成封面 HTML 文件。输入视频标题、核心卖点与风格偏好，Claude 自主设计封面构图并输出可截图的 HTML 文件。与 short-video-frames 配套使用，也可独立调用。
allowed-tools: [AskUserQuestion, Write, Read]
---

# short-video-cover

## 工作流

### Phase 0 — 信息收集

执行前确认以下输入（未提供的向用户询问）：

- **视频标题**（将成为封面主标题）
- **副标题 / 核心卖点**（一句话，10 字以内最佳）
- **项目关键数据**（可选，如 Stars 数、语言、类型标签）

---

### Phase 1 — 风格与规格确认

**使用 AskUserQuestion 工具进行交互式选择**：

```json
{
  "questions": [
    {
      "question": "请选择封面比例：",
      "header": "封面比例",
      "multiSelect": false,
      "options": [
        {
          "label": "16:9 横屏",
          "description": "1920 × 1080 — B 站横屏封面"
        },
        {
          "label": "3:4 竖屏",
          "description": "1080 × 1440 — 小红书封面"
        },
        {
          "label": "9:16 竖屏",
          "description": "1080 × 1920 — 抖音竖屏封面"
        }
      ]
    },
    {
      "question": "请选择美术风格（与画面帧保持一致）：",
      "header": "美术风格",
      "multiSelect": false,
      "options": [
        {
          "label": "1 · 极简白底",
          "description": "大量留白 + 细实边框"
        },
        {
          "label": "2 · 暗色技术感",
          "description": "深色层次 + 冷色强调 + 网格纹理"
        },
        {
          "label": "3 · 暖调书卷",
          "description": "#faf8f4 + 金色点缀"
        },
        {
          "label": "4 · 杂志对比",
          "description": "高对比度 + 粗重标题"
        }
      ]
    },
    {
      "question": "请选择封面元素（可多选）：",
      "header": "可选元素",
      "multiSelect": true,
      "options": [
        {
          "label": "Stars 数字大字",
          "description": "用特大字号展示 GitHub Stars 数"
        },
        {
          "label": "编程语言标签",
          "description": "显示项目主要编程语言"
        },
        {
          "label": "角标徽章",
          "description": "添加“开源推荐” “本周必看” 等角标"
        },
        {
          "label": "作者头像占位",
          "description": "预留区域供后期叠加头像"
        }
      ]
    }
  ]
}
```

等待用户选择后进入 Phase 2。

---

### Phase 2 — 封面 HTML 生成

**输出文件**：`<项目目录>/html/cover.html`

**硬性要求**：
- 固定宽高与所选比例一致
- 完全自包含，外部字体仅用 Google Fonts CDN
- 不使用本地路径 `<img>`
- 文件首行注释：`<!-- Cover | [视频标题摘要] | [风格代号] -->`

**封面设计原则**（Claude 自主执行）**：

封面的核心任务是在缩略图尺寸下（约 320px 宽）仍能清晰传递「这是什么、值不值得点进去」。设计时应当：

- 主标题字号足够大，缩略图下可读（建议不低于画面高度的 8%）
- 视觉重心明确，不超过 3 个信息层级
- 选用能在深色/浅色背景下均清晰的配色对比
- 可用 CSS 几何图形、数字大字、色块分割构建视觉张力
- 如果有 Stars 数字，用超大字号作为视觉锚点——数字本身就是卖点

---

### Phase 3 — 输出说明

```
已生成：<项目目录>/html/cover.html
在浏览器中打开审核样式。
满意后回复「导出封面」，导出到 <项目目录>/封面/cover.png。
```

---

## 注意

- 封面与视频帧是不同文件，不合并
- 若已执行 short-video-frames 且风格已确认，封面直接沿用，无需重复选择
- 导出由后续指令执行，本 skill 不自动触发

