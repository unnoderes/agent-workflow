# HTML Image Export Tools

Playwright-based tools for exporting HTML files to static images (PNG) and animated videos (WebM).

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Export HTML Files

**Parallel Export (Recommended for 3+ files)**:
```bash
npm run export:parallel -- --input-dir ./html --output-dir ./exports
```

**Serial Export (1-2 files)**:
```bash
# Copy HTML files to current directory first
cp ./html/*.html .
npm run export:screenshots
```

**Video Export (GSAP animations)**:
```bash
# Copy HTML files to current directory first
cp ./html/*.html .
npm run export:videos
```

## Available Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `export:parallel` | Batch PNG export (parallel) | `--input-dir <path>`, `--include <pattern>` | `--output-dir <path>` |
| `export:screenshots` | PNG export (serial, cwd) | `*.html` in cwd | `exports/*.png` |
| `export:videos` | WebM video export (cwd) | `*.html` in cwd | `video-exports/*.webm` |

## Performance

| Files | Serial | Parallel (3x) | Speedup |
|-------|--------|---------------|----------|
| 6 animated | ~90s | ~30s | **67%** |
| 10 animated | ~150s | ~50s | **67%** |

## Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command quick reference
- **[TEST.md](TEST.md)** - Testing guide and examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[PERFORMANCE_TEST.md](PERFORMANCE_TEST.md)** - Benchmark results

## Examples

### Parallel Export with Custom Concurrency

```bash
# Low-end device (2 browsers)
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 2

# High-end device (5 browsers)
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 5
```

### Batch Convert Videos to MP4

```bash
for file in video-exports/*.webm; do
  ffmpeg -i "$file" -c:v libx264 -c:a aac "${file%.webm}.mp4"
done
```

## Troubleshooting

### "No browser executable found"

`browser.js` searches the usual Chrome/Edge/Chromium locations for your
platform. To point at a specific binary, set `CHROME_PATH`:

```bash
export CHROME_PATH="/path/to/chrome"
```

Alternatively install one through Playwright: `npx playwright install chromium`.

### Memory Issues

Reduce concurrency:

```bash
npm run export:parallel -- --input-dir ./html --output-dir ./exports --concurrency 1
```

### Animation Not Captured

For GSAP animations, ensure you signal completion:

```javascript
gsap.to(element, {
  // ... animation properties
  onComplete: () => {
    window.gsapAnimationComplete = Promise.resolve();
  }
});
```

## Requirements

- Node.js 14+
- A Chromium-based browser (Chrome, Edge, Chromium or Brave), or one installed
  via `npx playwright install chromium`
- ~200 MB RAM per concurrent browser

## License

MIT
