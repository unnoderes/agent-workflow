# html-image-export

将 HTML 文件导出为静态图片（PNG）或动画视频（WebM），支持 GSAP 动画增强。

## 功能特性

- **静态截图导出**：将 HTML 文件截图为 PNG 图片（1920×1080）
- **动画视频导出**：录制 GSAP 动画为 WebM 视频（支持 VP9 编码）
- **自动化工作流**：通过 PowerShell 脚本一键完成项目初始化与导出
- **跨平台支持**：基于 Playwright，支持 Windows/macOS/Linux

## 快速开始

### 1. 准备 HTML 文件

将要导出的 HTML 文件放在目标目录中，例如：

```
video-frames/
  ├── frame_01.html
  ├── frame_02.html
  └── frame_03.html
```

### 2. 静态截图导出

```powershell
cd html-image-export/scripts
.\bootstrap-exporter.ps1 -TargetDir ..\..\video-frames
```

导出的 PNG 图片将保存在 `video-frames/exports/` 目录。

### 3. 动画视频导出

如果 HTML 中包含 GSAP 动画，可以导出为视频：

```powershell
cd html-image-export/scripts
.\bootstrap-exporter.ps1 -TargetDir ..\..\video-frames -ExportVideos
```

导出的 WebM 视频将保存在 `video-frames/video-exports/` 目录。

## GSAP 动画集成

### 基础模板

在 HTML 文件中添加 GSAP 动画：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      width: 1920px;
      height: 1080px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  </style>
</head>
<body data-animation-duration="3000">
  <h1>标题</h1>
  <p>内容</p>
  
  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
  <script>
    // 创建动画时间轴
    const tl = gsap.timeline();
    
    // 标题淡入 + 上移
    tl.from("h1", { 
      opacity: 0, 
      y: 50, 
      duration: 0.8 
    });
    
    // 正文逐段飞入
    tl.from("p", { 
      opacity: 0, 
      y: 50, 
      duration: 0.8, 
      stagger: 0.2,
      delay: 0.3 
    });
    
    // 标记动画完成（供 Playwright 使用）
    tl.to({}, {
      duration: 0,
      onComplete: () => document.body.classList.add('ready')
    });
  </script>
</body>
</html>
```

### 动画时长控制

**方法 1**：使用 `data-animation-duration` 属性（推荐）

```html
<body data-animation-duration="3500">
```

**方法 2**：在脚本末尾添加注释

```javascript
// total duration: 3500
```

**方法 3**：默认值（3000ms / 3秒）

如果未指定，录制时长为 3 秒。

### 完成标记（必需）

视频录制需要检测动画何时完成。在动画结束时添加 `ready` class：

```javascript
tl.to({}, {
  duration: 0,
  onComplete: () => document.body.classList.add('ready')
});
```

或使用 JavaScript：

```javascript
setTimeout(() => {
  document.body.classList.add('ready');
}, 3000);
```

## 常见动画模式

### P0：文字淡入 + 飞入

```javascript
gsap.from("h1", { opacity: 0, y: 50, duration: 0.8 });
gsap.from("p", { 
  opacity: 0, 
  y: 50, 
  duration: 0.8, 
  stagger: 0.2, 
  delay: 0.3 
});
```

### P1：图片缩放 / 淡入

```javascript
gsap.from(".image", { 
  opacity: 0, 
  scale: 0.8, 
  duration: 1.0, 
  ease: "back.out(1.2)" 
});
```

### P2：数字滚动增长

```javascript
gsap.from(".counter", {
  textContent: 0,
  duration: 1.5,
  snap: { textContent: 1 },
  onUpdate: function() {
    this.targets()[0].textContent = Math.round(this.targets()[0].textContent);
  }
});
```

### P3：背景渐变移动

```javascript
gsap.to("body", {
  backgroundPosition: "100% 100%",
  duration: 3,
  ease: "none"
});
```

## 导出参数说明

### bootstrap-exporter.ps1 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-TargetDir` | HTML 文件所在目录（必需） | - |
| `-ExportVideos` | 导出为视频而非截图 | `false` |
| `-ForceProjectSync` | 强制更新导出脚本 | `false` |

### 示例

```powershell
# 基础截图导出
.\bootstrap-exporter.ps1 -TargetDir ..\..\my-frames

# 视频导出
.\bootstrap-exporter.ps1 -TargetDir ..\..\my-frames -ExportVideos

# 强制更新脚本后导出视频
.\bootstrap-exporter.ps1 -TargetDir ..\..\my-frames -ExportVideos -ForceProjectSync
```

## 视频格式转换

导出的 WebM 视频使用 VP9 编码，如需转换为 MP4：

```bash
ffmpeg -i frame_01.webm -c:v libx264 -c:a aac frame_01.mp4
```

批量转换：

```bash
for file in video-exports/*.webm; do
  ffmpeg -i "$file" -c:v libx264 -c:a aac "${file%.webm}.mp4"
done
```

## 技术架构

```
html-image-export/
├── scripts/
│   └── bootstrap-exporter.ps1    # 主入口脚本
├── assets/
│   └── exporter-project/         # 导出器模板
│       ├── export-screenshots.js # 截图导出脚本
│       ├── export-videos.js      # 视频导出脚本
│       └── package.json          # 依赖配置
└── SKILL.md                      # 技能文档
```

### 工作流程

1. **项目初始化**：`bootstrap-exporter.ps1` 将导出器复制到目标目录
2. **依赖安装**：自动运行 `npm install playwright-core`
3. **文件扫描**：查找所有 `frame_*.html` 文件
4. **执行导出**：
   - 静态模式：调用 `export-screenshots.js`，截图最终状态
   - 视频模式：调用 `export-videos.js`，录制动画过程
5. **输出结果**：保存到 `exports/` 或 `video-exports/` 目录

## 注意事项

1. **HTML 尺寸**：确保 HTML 的 `<body>` 或容器设置为 1920×1080
2. **CDN 依赖**：GSAP 从 CDN 加载，需要网络连接
3. **动画完成标记**：视频录制依赖 `.ready` class，否则会超时
4. **录制时长**：避免动画过长（建议 2-5 秒），文件会很大
5. **Playwright 安装**：首次运行需要下载浏览器引擎（约 100MB）

## 故障排查

### 视频录制超时

**原因**：动画未添加完成标记

**解决**：在动画结束时添加：

```javascript
document.body.classList.add('ready');
```

### 视频文件过大

**原因**：动画时长过长或分辨率过高

**解决**：
- 缩短动画时长（建议 2-5 秒）
- 降低视频质量（需修改 `export-videos.js` 中的 `videoBitsPerSecond`）

### GSAP 动画不执行

**原因**：CDN 加载失败或脚本错误

**解决**：
- 检查网络连接
- 在浏览器中打开 HTML 文件，查看控制台错误
- 确认 GSAP CDN 地址可访问

## 集成到短视频制作流程

本工具是 `short-video-frames` 技能的配套导出器。完整流程：

1. **编写分段文案**
2. **使用 `short-video-frames` 技能生成 HTML**（支持 GSAP 动画）
3. **在浏览器中预览审核**
4. **使用本工具导出**：
   - 无动画 → 静态截图（PNG）
   - 有动画 → 视频录制（WebM）
5. **后期剪辑合成**（Premiere Pro / DaVinci Resolve）

## 许可证

MIT License