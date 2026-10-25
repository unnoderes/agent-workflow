---
name: short-video-frames
description: 将分段视频文案转化为可预览的 HTML 画面文件，支持 GSAP 动画效果。输入分段脚本,Claude 自主决定构图与视觉表达,识别哪些画面由自己生成、哪些建议用户手动截图,最终在审核通过后再决定是否导出图片或动画视频。适用于 GitHub 项目推荐类短视频的画面内容生产。
---

# short-video-frames

## 工作流

### Phase 0 — 画面解构

读取用户提供的分段文案,对每一段输出一行判断:

| 画面类型 | 由 Claude 生成 HTML | 建议用户手动截图 |
|----------|--------------------|--------------------|
| 标题卡 / 片头 / 片尾 CTA | ✓ | |
| 特性亮点、对比说明、数据指标 | ✓ | |
| 代码片段展示 | ✓ | |
| 流程示意、架构图（可用 SVG/CSS 表达） | ✓ | |
| 真实 GitHub 仓库页面 UI | | ✓ 需真实网页截图 |
| 实际运行效果 / 动效演示 | | ✓ 需录屏或软件截图 |
| 含第三方品牌 Logo 的场景 | | ✓ 需取用官方素材 |

输出摘要，列明分工，说明手动截图帧的建议截图方式。

---

### Phase 1 — 风格与规格确认

在开始生成前，向用户呈现以下选项，**等待选择后**再进入 Phase 2：

**画面比例**
- A · 16:9 横屏（1920 × 1080）— B 站 / YouTube
- B · 9:16 竖屏（1080 × 1920）— 抖音 / 小红书 Reels
- C · 1:1 方形（1080 × 1080）— 小红书图文

**美术风格**（每种风格都有完整的 Design System 规范，见下方详细说明）
- 1 · 极简白底（Minimal White）— 适合商业、产品、简洁教程
- 2 · 暗色技术感（Dark Tech）— 适合编程、技术、开发工具
- 3 · 暖调书卷（Warm Parchment）— 适合人文、设计、创意
- 4 · 杂志对比（Magazine Contrast）— 适合营销、品牌、对比测评
- 5 · 自定义（Custom）— 用户描述具体要求，Claude 自行诠释

---

### Phase 2 — HTML 文件生成

**输出目录**：`<项目目录>/html/`（由 `init-video-project` 创建；项目目录不存在时先运行它）

**文件命名**：`frame_01.html`、`frame_u002.html` …（手动截图帧跳过编号，用占位说明）

**每个文件的硬性要求**：
- 固定宽高与所选比例一致，画面区块居中于视口（`display:flex; align-items:center; justify-content:center; min-height:100vh`）
- 完全自包含，外部字体仅用 Google Fonts CDN
- 不使用本地路径 `<img>`，图形用 SVG / CSS shape / Unicode 字符替代
- 文件首行注释：`<!-- Frame N | [文案片段关键词] | [风格代号] -->`

---

#### 生成时必须遵守的规则

**一、严格按照选定风格的 Design System 生成**

- 在 Phase 1 用户选择风格后，**必须查阅该风格在本文档中的完整 Design System 规范**
- 直接复用规范中的 CSS 变量、字号、圆角、投影、间距值
- 不自行发明颜色值或尺寸，不要“近似”或“微调”

**二、模型主观能动性：视觉翻译而非排版文案**

Claude 在此阶段拥有完整的视觉决策权。文案是语义输入，而非排版稿——不要把文案文字直接堆到画面里。应当：

- 判断每帧的视觉重心在哪里，主动决定构图层次
- 选择最能传递该段情绪的颜色、字重、间距组合
- 用图形、线条、数字大字、引用块等方式做「视觉翻译」
- 若认为某段文案拆成 2 帧表达效果更好，可主动拆分并在总结中说明
- 可为有节奏感的画面加入 CSS 入场动画（`@keyframes`），但保持单个文件可静态截图
- **可使用 GSAP 动画库**添加更复杂的画面内元素动画（文字飞入、图片缩放、数字滚动等）

**三、视觉层次决策树**

每一帧必须先判断其信息类型，再选择对应的视觉处理方式：

```
① 标题卡 / 开场 / 结尾
   → 大字号标题（主标题字号） + 简短副标题 + 分隔线/徽章
   → 背景居中坐型，充足留白

② 数据 / 指标 / 对比
   → 特大数字（超大标题字号） + 小号单位或解释
   → 用强调色高亮关键数值
   → 对比型内容用分栏或分区块布局

③ 流程 / 步骤 / 时间线
   → 编号 + 简短文字 + 箭头/连线
   → 层叠卡片或垂直排列

④ 代码片段 / 终端模拟
   → 必须包含模拟标题栏（三点 + 路径/标题）
   → 使用 JetBrains Mono 字体
   → 代码内容用语法高亮颜色

⑤ 特性列举 / 功能点
   → 制作成多卡片或列表形式
   → 每个点有徽章/图标 + 标题 + 简述

⑥ 概念解释 / 抽象内容
   → 用 SVG 图形或简单图示辅助
   → 文字不超过 4 行，超出拆成两帧
```

---

**GSAP 动画集成指南**：

当需要更丰富的动画效果时，可以在 HTML 中集成 GSAP：

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
  // 标题淡入 + 上移
  gsap.from("h1", { opacity: 0, y: 50, duration: 0.8 });
  
  // 正文逐段飞入
  gsap.from("p", { 
    opacity: 0, 
    y: 50, 
    duration: 0.8, 
    stagger: 0.2, 
    delay: 0.3 
  });
  
  // 设置完成标记供 Playwright 视频录制使用
  gsap.to({}, {
    duration: 0,
    delay: 2.5, // 总动画时长
    onComplete: () => document.body.classList.add('ready')
  });
</script>
```

**动画优先级建议**：
- **P0（必需）**：标题、正文文字淡入 + 飞入效果
- **P1（推荐）**：图片缩放/淡入、关键元素强调
- **P2（可选）**：数字滚动增长（数据展示场景）
- **P3（点缀）**：背景渐变移动、装饰元素动画

**动画时长控制**：
- 在 `<body>` 标签添加 `data-animation-duration="[毫秒]"` 属性
- 或在脚本末尾添加注释 `// total duration: 2500`
- 默认为 3000ms（3秒）

**导出选项**：
- **静态截图**：使用 `html-image-export` 默认模式，动画会被快进到最终状态
- **动画视频**：使用 `html-image-export -ExportVideos` 模式，录制完整动画过程为 WebM 视频

---

### Phase 3 — 审核与导出说明

生成完毕后输出清单：

```
已生成 HTML 文件（<项目目录>/html/）：
  frame_01.html — [摘要]
  frame_02.html — [摘要]
  ...

需用户手动截图的画面：
  [Frame X] — 建议截图：[具体来源，如"github.com/xxx 仓库首页"]
  [Frame Y] — 建议截图：[建议录屏展示 xxx 功能]

在浏览器中打开 HTML 文件审核样式。
满意后回复：
- 「导出 frame_N」或「全部导出」触发静态截图流程
- 「导出动画视频」触发 GSAP 动画录制流程
```

截图/视频导出由后续指令执行，本 skill 不自动触发。

---

## 美术风格 Design System

> 每种风格的所有规范在 Phase 2 生成 HTML 时必须严格遵守。CSS 变量和模板直接复用。

---

### 风格 1 · 极简白底（Minimal White）

**适用场景**：产品介绍、商业内容、设计工具、简洁教程

**设计原则**：大量留白 + 内容集中 + 细节优先。任何迟豪要素都影响干净感。

#### 色彩系统

```css
:root {
  /* 背景 */
  --bg-primary:   #ffffff;
  --bg-secondary: #f7f8fa;   /* 卡片、代码块背景 */
  --bg-tertiary:  #eef0f3;   /* 分隔带、标签胎 */

  /* 文字 */
  --text-primary:   #0d0f12;  /* 主标题 */
  --text-secondary: #3d4451;  /* 副标题、正文 */
  --text-muted:     #8b919d;  /* 标注、次要信息 */
  --text-disabled:  #c4c9d1;

  /* 强调色（同时仅选一种） */
  --accent:       #0066ff;   /* 蓝色（默认） */
  --accent-light: #e8f0fe;   /* 轻重强调胎 */

  /* 边框 */
  --border:       #e2e5ea;
  --border-strong:#c8cdd6;
}
```

**备选强调色（根据内容主题选一种）**：
- 中性业务：`#0066ff`（蓝）
- 创意设计：`#7c3aed`（紫）
- 生产工具：`#059669`（绿）
- 数据分析：`#dc6803`（橙）

#### 字体系统

```
Google Fonts：
Inter — 全内容无衡线字
可选补充： Noto Serif SC — 大标题袆衡线字

字号对应 (9:16 特写)：
  主标题：  Inter 68-80px  weight 800  letter-spacing -2.5px  color: var(--text-primary)
  副标题：  Inter 40-52px  weight 700  letter-spacing -1.5px  color: var(--text-secondary)
  正文大：  Inter 28-34px  weight 400  letter-spacing -0.3px  color: var(--text-secondary)
  正文中：  Inter 24-28px  weight 400  color: var(--text-muted)
  标注：    Inter 18-22px  weight 400  color: var(--text-disabled)
```

#### 圆角 / 投影 / 间距

```css
/* 圆角 */
--radius-sm:  8px;   /* 小标签、徽章 */
--radius-md:  14px;  /* 中等卡片、按鈕 */
--radius-lg:  20px;  /* 大卡片、容器 */
--radius-xl:  28px;  /* 全宽帧内容区 */

/* 投影（极轻，不要深重） */
--shadow-sm:  0 1px 4px rgba(0,0,0,.06), 0 0 0 1px rgba(0,0,0,.04);
--shadow-md:  0 4px 12px rgba(0,0,0,.08), 0 0 0 1px rgba(0,0,0,.04);
--shadow-lg:  0 8px 24px rgba(0,0,0,.10), 0 0 0 1px rgba(0,0,0,.04);

/* 间距基础单元：8px */
--sp-xs:  8px;
--sp-sm: 16px;
--sp-md: 24px;
--sp-lg: 40px;
--sp-xl: 64px;

/* 内容区 padding（9:16） */
--page-pad-h: 72px;  /* 左右 */
--page-pad-v: 96px;  /* 上下 */
```

#### 布局原则

- 最多 3 层色彩，不用渐变背景和拼色块
- 切分线用细实边框（`1px solid var(--border)`），不用背景色块分段
- 大标题拥有充足空居，不拥挡
- 强调色仅用于最重要的 1-2 个元素
- 文字不超过 4 行（超出考虑拆分成两帧）
- 概念性内容优先用大字号 + 极少文字的组合

#### CSS 模板（8px 单元外包层）

```html
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 1080px; height: 1920px; overflow: hidden; }
  body {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    background: #ffffff;
    color: #0d0f12;
  }
  .page {
    width: 1080px; height: 1920px;
    padding: 96px 72px;
    display: flex; flex-direction: column; justify-content: center;
    gap: 40px;
  }
  /* 分隔线 */
  .divider { width: 48px; height: 3px; background: #0066ff; border-radius: 2px; }
  /* 卡片 */
  .card {
    background: #f7f8fa;
    border: 1px solid #e2e5ea;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0,0,0,.08);
  }
  /* 强调色文字 */
  .accent { color: #0066ff; }
  /* 标签 */
  .tag {
    display: inline-flex; align-items: center;
    padding: 8px 16px;
    background: #e8f0fe;
    color: #0066ff;
    border-radius: 8px;
    font-size: 20px; font-weight: 600;
  }
</style>
```

---

### 风格 2 · 暗色技术感（Dark Tech）

**适用场景**：开发工具、开源项目、编程教程、AI 产品

**设计原则**：深色层次建立空间感，冷色强调打点亮点，网格背景增加科技质地。

#### 色彩系统

```css
:root {
  /* 背景 */
  --bg-primary:   #080b0f;   /* 页面底色 */
  --bg-card:      #10151c;   /* 卡片背景 */
  --bg-elevated:  #151b24;   /* 标题栏、层叠元素 */

  /* 文字 */
  --text-primary:   #e8eef5;  /* 主要文字 */
  --text-secondary: #a8b4c4;  /* 次要文字 */
  --text-muted:     #7a8699;  /* 阱尼文字、标注 */
  --text-code:      #dbe6f0;  /* 代码、数据 */

  /* 强调色 */
  --accent:       #35e0b0;   /* 青绻强调（默认） */
  --accent-dim:   rgba(53,224,176,.12);  /* 强调色轻底色 */
  --accent-glow:  rgba(53,224,176,.18);  /* 发光效果 */
  --warn:         #f2b544;   /* 警告色 */
  --danger:       #f2607a;   /* 错误色 */

  /* 边框 */
  --border:       #232c38;   /* 默认边框 */
  --border-accent:#2b5a4c;   /* 强调色边框 */
}
```

**备选强调色（根据内容主题选一种）**：
- AI / 编程工具：`#35e0b0`（青绻，默认）
- 系统 / 基础设施：`#4f9bff`（蓝）
- 安全 / 加密：`#a78bfa`（紫）
- 性能 / 数据：`#fb923c`（橙）

#### 背景层次

```css
/* 基础背景（必用） */
body {
  background: #080b0f;
}

/* 顶部聚光（可选） */
body::after {
  content: '';
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(800px 600px at 50% -4%, #18242f 0%, transparent 64%),
    radial-gradient(700px 600px at 50% 108%, rgba(53,224,176,.10) 0%, transparent 62%);
}

/* 网格纹理（可选） */
body::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
  background-size: 64px 64px;
  -webkit-mask-image: radial-gradient(90% 76% at 50% 44%, #000 24%, transparent 100%);
          mask-image: radial-gradient(90% 76% at 50% 44%, #000 24%, transparent 100%);
}
```

**常用背景变体**：
- A · 单点聚光：顶部冷色渐变（需要效果简单时用）
- B · 双点对角：顶部冷色 + 底部强调色（常用）
- C · 红色冷山岁掛：将第二个 `radial-gradient` 的颜色换为 `rgba(242,96,122,.12)` （用于痛点/失败场景）

#### 字体系统

```
Google Fonts：
Inter — 标题和正文
JetBrains Mono — 数据、代码、标签、帧编号

字号对应 (9:16 特写)：
  主标题：  Inter 62-78px  weight 900  letter-spacing -2px    color: var(--text-primary)
  副标题：  Inter 40-52px  weight 800  letter-spacing -1.5px  color: var(--text-primary)
  正文大：  Inter 28-34px  weight 500  letter-spacing -0.3px  color: var(--text-secondary)
  正文中：  Inter 22-27px  weight 400                         color: var(--text-muted)
  代码/数据： JetBrains Mono 20-27px  weight 500             color: var(--text-code)
  标签/帧号： JetBrains Mono 18-22px  weight 700             color: var(--text-muted)

标题渐变手法（可选）：
  .gradient-text {
    background: linear-gradient(180deg, #fff 40%, #8fb6c9 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
```

#### 圆角 / 投影 / 间距

```css
/* 圆角 */
--radius-sm:  10px;  /* 小徽章、点个 */
--radius-md:  16px;  /* 中等卡片、内嵌元素 */
--radius-lg:  20px;  /* 主卡片、容器 */
--radius-xl:  28px;  /* 全宽模拟窗口 */
--radius-pill: 9999px; /* 胶囊形标签 */

/* 投影（深色调） */
--shadow-card:   0 12px 32px rgba(0,0,0,.5), inset 0 0 0 1px rgba(255,255,255,.02);
--shadow-float:  0 34px 70px rgba(0,0,0,.6), inset 0 0 0 1px rgba(255,255,255,.02);
--shadow-accent: 0 0 24px rgba(53,224,176,.20);  /* 强调色发光 */

/* 间距基础单元：8px */
--sp-xs:  8px;
--sp-sm: 16px;
--sp-md: 24px;
--sp-lg: 40px;
--sp-xl: 64px;

/* 内容区 padding（9:16） */
--page-pad-h: 68-76px;  /* 左右 */
--page-pad-v: 88-96px;  /* 上下 */
```

#### 常用组件模板

```css
/* 主卡片 */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 30px 32px;
  box-shadow: var(--shadow-card);
}

/* 强调色卡片（带强调色边框） */
.card-accent {
  background: var(--bg-card);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius-lg);
  box-shadow: 0 0 0 1px var(--accent-glow) inset, var(--shadow-card);
}

/* 左侧强调线卡片 */
.card-lined {
  position: relative;
  padding-left: 32px;
}
.card-lined::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
  background: linear-gradient(180deg, var(--accent), rgba(53,224,176,.3));
  border-radius: 2px;
}

/* 帧头数字+标签 */
.frame-header {
  display: flex; align-items: baseline; justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
}
.frame-num { font-size: 24px; color: var(--text-muted); }
.frame-num b { color: var(--accent); font-weight: 700; }
.frame-tag {
  font-size: 20px; letter-spacing: 6px; color: var(--text-muted);
  padding: 10px 20px; border: 1px solid var(--border); border-radius: var(--radius-pill);
}

/* 胶囊形强调标签 */
.badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 18px;
  background: var(--accent-dim);
  color: var(--accent);
  border: 1px solid rgba(53,224,176,.3);
  border-radius: var(--radius-pill);
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px; font-weight: 600; letter-spacing: 2px;
}
```

#### 布局原则

- 每帧必须包含层次：背景层 → 主内容层 → 强调元素，至少 3 层深度
- 强调色（#35e0b0）只用于最重要的 1-2 个元素，不要濮渋
- 大标题优先使用渐变手法（`.gradient-text`）
- 模拟 UI 展示时（终端、代码块）应正确包含模拟标题栏三点
- 在不确定用哪种背景变体时，优先选 B（双点对角）

---

### 风格 3 · 暖调书卷（Warm Parchment）

**适用场景**：人文科普、读书心得、设计思考、文字内容为主的视频

**设计原则**：纸张质地 + 温肖肉色躺 + 殯线标题 + 金属色点缀。

#### 色彩系统

```css
:root {
  /* 背景 */
  --bg-primary:   #faf8f4;   /* 米白纸张底 */
  --bg-secondary: #f3f0e8;   /* 稍深躺色卡片 */
  --bg-tertiary:  #ebe6d6;   /* 次要分隔 */

  /* 文字 */
  --text-primary:   #2c2318;  /* 深茶 */
  --text-secondary: #5c4a32;  /* 中茶 */
  --text-muted:     #9c8060;  /* 浅孙 */

  /* 强调色 */
  --accent:       #b8860b;   /* 暗金色（默认） */
  --accent-light: #f5e6c0;   /* 金色渡阵底 */
  --accent-rust:  #a0522d;   /* 锤 色（备选强调） */

  /* 边框 */
  --border:       #d9d0bc;
  --border-strong:#b8a888;
}
```

#### 字体系统

```
Google Fonts：
Noto Serif SC — 主标题（袆衡线字）
Inter — 正文和辅助文字

字号对应 (9:16 特写)：
  主标题：  Noto Serif SC  68-80px  weight 900  letter-spacing -1px  color: var(--text-primary)
  副标题：  Noto Serif SC  40-52px  weight 700  letter-spacing -0.5px color: var(--text-secondary)
  引言大字： Noto Serif SC  80-96px  weight 900  仅展示少量关键词
  正文：    Inter          26-32px  weight 400  letter-spacing 0.2px  color: var(--text-secondary)
  标注：    Inter          20-22px  weight 400  color: var(--text-muted)
  强调词：   Noto Serif SC  相同字号   weight 700  color: var(--accent)
```

#### 圆角 / 投影 / 间距

```css
/* 圆角（偏方，体现书卷气质） */
--radius-sm:  6px;
--radius-md:  12px;
--radius-lg:  16px;

/* 投影（暖色调、有场景感） */
--shadow-sm:  0 2px 6px rgba(80,52,20,.08);
--shadow-md:  0 6px 20px rgba(80,52,20,.12);
--shadow-lg:  0 12px 36px rgba(80,52,20,.16);

/* 间距 */
--sp-xs:  8px;
--sp-sm: 16px;
--sp-md: 28px;
--sp-lg: 48px;
--sp-xl: 72px;

/* 内容区 padding */
--page-pad-h: 80px;
--page-pad-v: 104px;
```

#### 布局原则

- 标题优先使用袆衡线字（Noto Serif SC），与正文 Inter 形成对比
- 点缀用金属色（`var(--accent)`），不用其他颜色
- 卡片内容可用淡金色底色（`var(--accent-light)`）凬造手写笔记氟围
- 避免使用冷色和高饱和度颜色
- 具有足够的段落间距，促进阅读节奏

---

### 风格 4 · 杂志对比（Magazine Contrast）

**适用场景**：对比测评、品牌分析、产品发布、营销内容

**设计原则**：高对比度 + 粗重标题 + 强版式感 + 类 Vercel/Linear 的现代感。

#### 色彩系统

```css
:root {
  /* 双色背景系统（黑 / 白分局） */
  --bg-dark:    #0a0a0a;   /* 深色区块 */
  --bg-light:   #f4f4f5;   /* 浅色区块 */
  --bg-white:   #ffffff;

  /* 文字 */
  --text-on-dark:  #ffffff;
  --text-on-light: #09090b;
  --text-muted:    #71717a;

  /* 强调色（高饱和，与黑白形成三色对比） */
  --accent:       #18181b;  /* 默认用黑色强调 */
  /* 备选鲜色强调： */
  /* --accent: #e11d48; */  /* 红（强强对比） */
  /* --accent: #2563eb; */  /* 蓝（科技产品） */
  /* --accent: #7c3aed; */  /* 紫（创意品牌） */

  /* 边框 */
  --border-dark:  #27272a;
  --border-light: #d4d4d8;
}
```

#### 字体系统

```
Google Fonts：
Inter — 主标题和正文
备选 Syne / Space Grotesk — 大标题（需要迟豪感时）

字号对应 (9:16 特写)：
  超大标题： Inter 80-120px weight 900  letter-spacing -4px  生成调度充充充充
  大标题：  Inter 60-80px  weight 900  letter-spacing -3px
  副标题：  Inter 36-48px  weight 700  letter-spacing -1.5px
  正文：    Inter 24-30px  weight 400  letter-spacing -0.3px
  标签：    Inter 16-20px  weight 600  letter-spacing 3-6px  大写
```

#### 圆角 / 投影 / 间距

```css
/* 圆角（倾向直角，强调干緹感） */
--radius-sm:  4px;
--radius-md:  8px;
--radius-lg:  12px;  /* 常用最大圆角 */

/* 投影（黑白，强列） */
--shadow-sm:  0 1px 3px rgba(0,0,0,.15), 0 1px 2px rgba(0,0,0,.10);
--shadow-md:  0 4px 8px rgba(0,0,0,.20), 0 2px 4px rgba(0,0,0,.12);
--shadow-lg:  0 20px 40px rgba(0,0,0,.30);

/* 间距（宼松，体现杂志气质） */
--sp-xs:  8px;
--sp-sm: 20px;
--sp-md: 36px;
--sp-lg: 56px;
--sp-xl: 88px;

--page-pad-h: 64px;
--page-pad-v: 80px;
```

#### 布局原则

- 分局核心：将帧划分为黑色区和白色区，形成强列
- 标题字号要大、大得够，充分利用缩放对比
- 文字与图形元素混排，不要纯文字布局
- 外边距要宽，内容紧凑，形成张力
- 在选择强调色时，要保证在黑色和白色区块上都有足够对比度

---

### 风格 5 · 自定义（Custom）

**适用场景**：以上风格都不符合时，或有非常具体的品牌视觉要求

**工作方式**：用户描述具体要求，Claude 基于以下框架自行诠释：

```
用户输入示例：
  "深蓝色，平静且岂优雅，类似苹果官网的首页风格"
  "橘色强调，针对年轻用户，活泼有活力"
  "很极简，黑白为主，只保留最关键的内容"

Claude 诠释时将定义并提前展示：
  1. 主背景色 / 强调色
  2. 标题字体选择
  3. 圆角大小框架
  4. 一帧展示效果预览，等用户确认后全量生成
```

**必须遵守的正交规则**（任何风格都适用）：
- 必须先生成一帧预览，等用户确认风格后再全量生成
- 配色数量不超过 3 种（主色 + 强调色 + 中性色）
- 主要内容区域的左右 padding 不小于 56px
- 字体不超过 2 种

---

### 有效帧设计通用反例

不论选择哪种风格，以下设计错误永远不应出现：

```
✗ 将文案文字直接堆到画面里（应做「视觉翻译」，不是排版）
✗ 同一帧中使用超过 4 种颜色
✗ 字号小于 18px（导出成范围内可读性不足）
✗ 网格背景在不需要科技感的风格中强行使用
✗ 学习内容类型的帧能翻生其他风格的模拟 UI（既不符合风格又影响信息传达）
✗ 每帧的内容布局完全相同、没有差异化
✗ 细节元素与主体内容纵讽等大，缺少视觉层次
```
