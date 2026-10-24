# Architecture: Parallel Export

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    export-parallel.js                        │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │  Parse CLI Args │
                    └───────┬─────────┘
                            │
                    ┌───────▼────────┐
                    │ Scan HTML Files │
                    └───────┬─────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────▼─────┐ ┌──────▼──────┐ ┌─────▼──────┐
    │  Browser 1  │ │  Browser 2  │ │  Browser 3 │
    │  (Chromium) │ │  (Chromium) │ │  (Chromium)│
    └───────┬─────┘ └──────┬──────┘ └─────┬──────┘
            │               │               │
    ┌───────▼─────┐ ┌──────▼──────┐ ┌─────▼──────┐
    │ frame_01    │ │ frame_02    │ │ cover      │
    │ frame_04    │ │ frame_05    │ │ frame_03   │
    └───────┬─────┘ └──────┬──────┘ └─────┬──────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                    ┌───────▼────────┐
                    │  Collect Results│
                    └───────┬─────────┘
                            │
                    ┌───────▼────────┐
                    │ Report Summary  │
                    └─────────────────┘
```

## Data Flow

### 1. Initialization Phase

```javascript
// Input validation
parseArgs() → { inputDir, outputDir, concurrency }

// File discovery
scanHtmlFiles(inputDir) → ["cover.html", "frame_01.html", ...]

// Browser pool creation
launchBrowsers(concurrency) → [browser1, browser2, browser3]
```

### 2. Task Distribution (Round-Robin)

```
Files: [cover, frame_01, frame_02, frame_03, frame_04, frame_05]
                    ↓
        ┌───────────┼───────────┐
        │           │           │
    Browser 1   Browser 2   Browser 3
        │           │           │
      cover     frame_01    frame_02
    frame_03    frame_04    frame_05
```

Algorithm:
```javascript
tasks = files.map((file, index) => ({
  file,
  browserIndex: index % concurrency
}))
```

### 3. Parallel Processing

Each browser processes its assigned files **sequentially**, but all browsers run **in parallel**:

```
Time →
  0s ┌─────────┬─────────┬─────────┐
     │Browser 1│Browser 2│Browser 3│
     ├─────────┼─────────┼─────────┤
  5s │ cover   │frame_01 │frame_02 │
     ├─────────┼─────────┼─────────┤
 10s │frame_03 │frame_04 │frame_05 │
     └─────────┴─────────┴─────────┘
     ↓
   Total: ~10s (vs 30s serial)
```

### 4. Per-File Export Pipeline

```
HTML File
    ↓
┌───────────────────────┐
│ Open in Browser Page  │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│  Load & Parse HTML    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│   Wait for Fonts      │
└───────────┬───────────┘
            ↓
      ┌─────┴─────┐
      │Has GSAP?  │
      └─────┬─────┘
      Yes   │   No
        │   │
        ▼   ▼
    ┌───────────┐   ┌──────────────┐
    │Wait GSAP  │   │Finish CSS    │
    │Animation  │   │Animations    │
    └─────┬─────┘   └──────┬───────┘
          │                │
          └────────┬───────┘
                   ▼
         ┌─────────────────┐
         │ Take Screenshot │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │  Save as PNG    │
         └─────────────────┘
```

## Animation Detection

### CSS Animation Handling

```javascript
// 1. Finish all running animations
for (const animation of document.getAnimations()) {
  animation.finish();
}

// 2. Force final states
for (const element of document.querySelectorAll("*")) {
  if (style.opacity === "0") element.style.opacity = "1";
  if (style.transform !== "none") element.style.transform = "none";
}
```

### GSAP Animation Handling

```javascript
// Check for GSAP presence
const hasGsap = typeof window.gsap !== "undefined" || 
                window.gsapAnimationComplete !== undefined;

if (hasGsap) {
  // Wait for animation complete signal
  await Promise.race([
    window.gsapAnimationComplete,  // Set by page: gsap.to(..., { onComplete })
    page.waitForTimeout(duration + 1000)  // Or timeout
  ]);
}
```

## Error Handling Strategy

### File-Level Isolation

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Browser 1│  │ Browser 2│  │ Browser 3│
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ▼             ▼             ▼
  ┌─────┐      ┌─────┐      ┌─────┐
  │File1│      │File2│      │File3│ ✗ Error!
  └──┬──┘      └──┬──┘      └──┬──┘
     │             │             │
     ▼             ▼             ▼
  { success }   { success }   { error }
                                  │
                                  └─→ Continues!
```

Error in one file **does not stop** other exports:

```javascript
try {
  await exportFile(browser, file);
  return { success: true, fileName };
} catch (error) {
  return { success: false, fileName, error: error.message };
}
```

### Error Summary Report

```
Export complete: 5/6 succeeded

Failed files (1):
  - broken.html: Navigation timeout exceeded
```

## Performance Characteristics

### Time Complexity

**Serial**: `O(n × t)` where:
- `n` = number of files
- `t` = average render time per file

**Parallel**: `O(⌈n/c⌉ × t + overhead)` where:
- `c` = concurrency level
- `overhead` ≈ 1.5s (browser launch)

### Space Complexity

**Memory**: `O(c × m)` where:
- `c` = concurrency level
- `m` ≈ 150-200 MB per browser instance

Example: `concurrency=3` → ~500 MB RAM usage

### Optimal Concurrency Formula

```
optimal_c = min(
  file_count,           // No point having more browsers than files
  CPU_cores - 1,        // Leave 1 core for system
  floor(RAM_GB / 0.2)   // Each browser needs ~200 MB
)
```

Examples:
- 6 files, 4-core CPU, 8GB RAM: `min(6, 3, 40)` = **3** ✅
- 10 files, 8-core CPU, 16GB RAM: `min(10, 7, 80)` = **7** ✅
- 20 files, 4-core CPU, 4GB RAM: `min(20, 3, 20)` = **3** ✅

## Comparison: Serial vs Parallel

### Serial (export-screenshots.js)

```
Single browser, sequential processing:

Browser 1: file1 → file2 → file3 → file4 → file5 → file6
           [===][===][===][===][===][===]
           
Total: 6 × 15s = 90s
```

### Parallel (export-parallel.js, concurrency=3)

```
Three browsers, parallel processing:

Browser 1: file1 → file4
           [===]  [===]
           
Browser 2: file2 → file5
           [===]  [===]
           
Browser 3: file3 → file6
           [===]  [===]
           
Total: 2 × 15s + overhead ≈ 32s
Speedup: 90s → 32s = 64% faster
```

## Code Structure

```
export-parallel.js
├── parseArgs()                 # CLI argument parsing
├── compileInclude()            # --include filename pattern filter
├── scanHtmlFiles()             # Input directory scanning
├── inferViewport()             # HTML viewport detection
├── inferAnimationDuration()    # Animation timing detection
├── settlePage()                # Animation completion logic
├── exportFile()                # Single file export
├── processBatch()              # Batch processing per browser
├── exportParallel()            # Main parallel orchestration
└── main()                      # Entry point

browser.js
├── resolveBrowserPath()        # Platform-aware browser discovery (+ CHROME_PATH)
└── launchOptions()             # chromium.launch() options
```

## Integration Points

### Input Interface

```bash
npm run export:parallel -- \
  --input-dir <path>      # Required: HTML source directory
  --output-dir <path>     # Required: PNG output directory
  --concurrency <n>       # Optional: Browser count (default: 3)
```

### Output Interface

```
Stdout: Progress logs
  [Browser 1] Exported cover.html
  [Browser 2] Exported frame_01.html
  ...
  
Stdout: Summary report
  Export complete: 6/6 succeeded
  Elapsed time: 2.5s
  
Exit code: 0 (success), 1 (fatal error)

Files: <output-dir>/*.png
```

## Future Enhancements

1. **Auto-tuning**: Detect system resources and set optimal concurrency
2. **Retry mechanism**: Automatically retry failed exports with backoff
3. 
