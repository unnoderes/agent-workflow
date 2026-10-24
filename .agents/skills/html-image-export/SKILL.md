---
name: html-image-export
description: Export one or more local HTML files into static PNG images or animated WebM videos. Use when Codex needs to batch render HTML mockups, slides, posters, covers, or other visual pages to images or videos, especially when the pages contain CSS animations, delayed reveals, transitions, or GSAP animations that need to be captured as video.
---

# HTML Image Export

Use the bundled exporter project to render local `.html` files into stable `.png` outputs or animated `.webm` videos.

Prefer this skill when:
- The working directory contains standalone HTML pages that need image or video export.
- The pages use CSS `animation`, `transition`, delayed `opacity`, transform-based entry effects, or GSAP animations.
- Normal screenshots would capture partially revealed content.
- You need to record GSAP animations as video files.

## Workflow

1. Confirm the target directory that contains the `.html` files.
2. Use `scripts/bootstrap-exporter.ps1` to deploy the bundled exporter project into that directory.
3. Let the script install `playwright-core` if needed.
4. Run the exporter in screenshot mode (default), parallel mode (recommended for batch), or video mode (`-ExportVideos` flag).
5. Spot-check a few generated images or videos. If a page still renders incompletely, read [references/troubleshooting.md](references/troubleshooting.md).

## Command

### Parallel Export (Recommended for Batch)

For exporting multiple HTML files, parallel mode reduces export time by 60-70%.

**Bash**:
```bash
cd <skill-dir>/assets/exporter-project
npm run export:parallel -- --input-dir /path/to/html --output-dir /path/to/output
```

**PowerShell**:
```powershell
cd <skill-dir>\assets\exporter-project
npm run export:parallel -- --input-dir C:\path\to\html --output-dir C:\path\to\output
```

#### Selecting Which Files a Run Picks Up

A source directory usually holds both the frame pages and the cover, while the
two have to land in different output directories. `--include` takes a
comma-separated list of `*` / `?` filename patterns (default `*.html`):

```bash
npm run export:parallel -- --input-dir <html> --output-dir <画面> --include "frame_*.html"
npm run export:parallel -- --input-dir <html> --output-dir <封面> --include cover.html
```

A pattern that matches nothing is an error, not a silent no-op.

#### Adjusting Concurrency

Tune concurrency based on device performance:

- **Low-end devices** (4GB RAM): `--concurrency 1` or `2`
- **Standard devices** (8GB RAM): `--concurrency 3` (default)
- **High-end devices** (16GB+ RAM): `--concurrency 5` or higher

Example:
```bash
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 5
```

`<skill-dir>` is this skill's own directory; substitute its absolute path.

#### Performance Comparison

| File Count | Serial Export | Parallel Export (3 concurrent) | Speedup |
|------------|---------------|--------------------------------|---------|
| 5 frames + 1 cover | ~90s | ~30s | 67% |
| 10 frames | ~150s | ~50s | 67% |

#### When to Use Serial Mode

- Device has limited memory (< 4GB)
- Debugging a single file issue
- HTML file count ≤ 2

### Screenshot Export (Single File / Serial)

For single file or low-concurrency exports, use the original serial mode:

Run the wrapper script:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>"
```

Optional flags:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>" -InstallDeps -ForceProjectSync
```

- `-InstallDeps`: Force `npm install` even if `node_modules/playwright-core` already exists.
- `-ForceProjectSync`: Overwrite the bundled exporter files in the target directory with the current skill version.

### Video Export (GSAP Animations)

To export HTML files with GSAP animations as WebM videos:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>" -ExportVideos
```

Combine with other flags as needed:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>" -ExportVideos -InstallDeps -ForceProjectSync
```

## Tool Layer

- `assets/exporter-project/package.json`: Minimal Node project used for export.
- `assets/exporter-project/browser.js`: Locates a Chromium-based executable on Windows, macOS or Linux; set `CHROME_PATH` to override, or install one with `npx playwright install chromium`.
- `assets/exporter-project/export-screenshots.js`: Browser automation script that waits for fonts, finishes animations, and forces invisible animation-start elements into their visible final state before taking screenshots.
- `assets/exporter-project/export-parallel.js`: Same capture, spread over N browsers with per-file error isolation and an `--include` filename filter.
- `assets/exporter-project/export-videos.js`: Browser automation script that records HTML pages with GSAP animations as WebM videos using Playwright's video recording API.
- `scripts/bootstrap-exporter.ps1`: Copies the whole tool project into the target directory, installs dependencies there, and runs the export.

## Output

### Screenshot Mode
`--output-dir` decides where the PNGs go; in the video pipeline that is
`<project-dir>/画面` for the frames and `<project-dir>/封面` for the cover. The
bootstrap wrapper defaults to an `exports/` folder inside the source directory
when no other output is given.

### Video Mode
The exporter writes:
- `<target-dir>\video-exports\*.webm`

The wrapper also places the reusable tool files in the target directory:
- `<target-dir>\package.json`
- `<target-dir>\browser.js`
- `<target-dir>\export-screenshots.js`
- `<target-dir>\export-parallel.js`
- `<target-dir>\export-videos.js`

Preserve existing user HTML files. Do not rewrite source pages just to disable animation unless troubleshooting proves the renderer cannot recover the final state at runtime.

## Animation Duration Control

For video export, the script automatically detects animation duration using these methods (in order of priority):

1. **Explicit duration attribute**: Add `data-animation-duration="3000"` to the `<body>` tag (milliseconds)
2. **Duration comment**: Add a comment `// total duration: 3000` in the GSAP script
3. **Default**: 3000ms (3 seconds) if no duration is specified

The script waits for the animation to complete by:
- Checking for `.animation-complete.ready` class on the body
- Or waiting for the specified duration + 1 second buffer

Example HTML with duration control:

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
</head>
<body data-animation-duration="2500">
  <h1>Title</h1>
  <script>
    gsap.from("h1", { 
      opacity: 0, 
      y: 50, 
      duration: 0.8,
      onComplete: () => document.body.classList.add('ready')
    });
  </script>
</body>
</html>
```

## Video Format Conversion

Videos are exported as WebM format. To convert to MP4 for wider compatibility, use FFmpeg:

```bash
ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4
```

Or batch convert all WebM files:

```bash
for file in *.webm; do ffmpeg -i "$file" -c:v libx264 -c:a aac "${file%.webm}.mp4"; done
```
