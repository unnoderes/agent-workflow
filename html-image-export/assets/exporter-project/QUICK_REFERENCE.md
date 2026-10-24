# Quick Reference: Parallel Export

## Installation

```bash
cd html-image-export/assets/exporter-project
npm install
```

## Basic Usage

```bash
npm run export:parallel -- --input-dir <html-dir> --output-dir <output-dir>
```

## Examples

### Default (3 concurrent browsers)

```bash
npm run export:parallel -- --input-dir ./html --output-dir ./画面
```

### Low-end device (2 browsers)

```bash
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 2
```

### High-end device (5 browsers)

```bash
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 5
```

## Performance

| File Count | Serial | Parallel (3x) | Speedup |
|------------|--------|---------------|----------|
| 6 animated files | ~90s | ~30s | 67% |
| 10 animated files | ~150s | ~50s | 67% |

## When to Use

### Use Parallel ✅
- 3+ HTML files
- Files have animations
- System: 4GB+ RAM

### Use Serial ⚠️
- 1-2 files only
- Static HTML (no animations)
- Low memory (< 4GB)
- Debugging issues

## Concurrency Guide

| RAM | Recommended |
|-----|-------------|
| 4GB | `--concurrency 2` |
| 8GB | `--concurrency 3` (default) |
| 16GB+ | `--concurrency 5-7` |

## Troubleshooting

### "No Chrome/Edge executable found"

Edit `export-parallel.js` and add your browser path:

```javascript
const browserCandidates = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  // Add your path here
];
```

### Memory issues / browser crashes

Reduce concurrency:

```bash
npm run export:parallel -- --input-dir ./html --output-dir ./画面 --concurrency 1
```

## Full Documentation

- **SKILL.md**: Complete usage guide
- **TEST.md**: Testing instructions
- **PERFORMANCE_TEST.md**: Benchmark results
- **IMPLEMENTATION_REPORT.md**: Technical details
