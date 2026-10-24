# Test Guide for Parallel Export

This guide walks through testing the parallel export functionality.

## Prerequisites

1. Node.js installed
2. Dependencies installed: `npm install` in this directory
3. A Chromium-based browser installed (or `npx playwright install chromium`)

## Step 1: Create Test HTML Files

Create a test directory with sample HTML files:

### Bash
```bash
mkdir -p test-html test-output

# Create 5 test frames with different background colors
for i in {1..5}; do
  cat > test-html/frame_0$i.html <<EOF
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 1080px;
      height: 1920px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Arial', sans-serif;
      font-size: 120px;
      font-weight: bold;
      color: white;
      text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
      background: linear-gradient(135deg, hsl($(($i * 60)), 80%, 50%), hsl($(($i * 60 + 30)), 80%, 60%));
    }
  </style>
</head>
<body>
  <div>Frame $i</div>
</body>
</html>
EOF
done

# Create a cover file
cat > test-html/cover.html <<EOF
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 1080px;
      height: 1920px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: 'Arial', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    h1 {
      font-size: 120px;
      margin: 0;
      text-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }
    p {
      font-size: 60px;
      margin-top: 40px;
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <h1>Cover Page</h1>
  <p>Test Export</p>
</body>
</html>
EOF

echo "Created 6 test HTML files in test-html/"
```

### PowerShell
```powershell
# Create test directories
New-Item -ItemType Directory -Force -Path test-html, test-output | Out-Null

# Create 5 test frames with different background colors
1..5 | ForEach-Object {
  $i = $_
  $hue = $i * 60
  $hue2 = $hue + 30
  
  @"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 1080px;
      height: 1920px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Arial', sans-serif;
      font-size: 120px;
      font-weight: bold;
      color: white;
      text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
      background: linear-gradient(135deg, hsl($hue, 80%, 50%), hsl($hue2, 80%, 60%));
    }
  </style>
</head>
<body>
  <div>Frame $i</div>
</body>
</html>
"@ | Out-File -FilePath "test-html/frame_0$i.html" -Encoding UTF8
}

# Create a cover file
@"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 1080px;
      height: 1920px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: 'Arial', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    h1 {
      font-size: 120px;
      margin: 0;
      text-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }
    p {
      font-size: 60px;
      margin-top: 40px;
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <h1>Cover Page</h1>
  <p>Test Export</p>
</body>
</html>
"@ | Out-File -FilePath "test-html/cover.html" -Encoding UTF8

Write-Host "Created 6 test HTML files in test-html/"
```

## Step 2: Run Parallel Export Test

### Test with Default Concurrency (3)

**Bash**:
```bash
time npm run export:parallel -- --input-dir test-html --output-dir test-output
```

**PowerShell**:
```powershell
Measure-Command {
  npm run export:parallel -- --input-dir test-html --output-dir test-output
}
```

### Test with Different Concurrency Levels

**Concurrency 1 (Serial-like)**:
```bash
rm -rf test-output/* # Clean output
time npm run export:parallel -- --input-dir test-html --output-dir test-output --concurrency 1
```

**Concurrency 5 (High-end)**:
```bash
rm -rf test-output/* # Clean output
time npm run export:parallel -- --input-dir test-html --output-dir test-output --concurrency 5
```

## Step 3: Verify Results

### Check PNG Count

**Bash**:
```bash
ls -lh test-output/*.png | wc -l
# Expected: 6 files
```

**PowerShell**:
```powershell
(Get-ChildItem test-output/*.png).Count
# Expected: 6 files
```

### Check File Sizes

**Bash**:
```bash
ls -lh test-output/*.png
# Each file should be > 100 KB (actual images, not blank)
```

**PowerShell**:
```powershell
Get-ChildItem test-output/*.png | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 2)}}
```

### Visual Inspection

Open the PNG files in an image viewer and verify:
- `frame_01.png` to `frame_05.png` show different gradient backgrounds
- Each frame displays "Frame N" text
- `cover.png` shows "Cover Page" title
- All images are 1080x1920 pixels

## Step 4: Performance Comparison

Compare serial vs parallel execution time:

### Serial Mode (Original export-screenshots.js)

**Bash**:
```bash
# Copy HTML files to current directory (export-screenshots.js expects files in cwd)
cp test-html/*.html .
time node export-screenshots.js
rm *.html # Clean up
```

**PowerShell**:
```powershell
# Copy HTML files to current directory
Copy-Item test-html/*.html .
Measure-Command { node export-screenshots.js }
Remove-Item *.html # Clean up
```

### Parallel Mode (3 concurrent browsers)

```bash
time npm run export:parallel -- --input-dir test-html --output-dir test-output
```

### Expected Results

| Mode | 6 Files (5 frames + 1 cover) |
|------|------------------------------|
| Serial | ~90 seconds |
| Parallel (concurrency=3) | ~30-40 seconds |
| **Speedup** | **60-67%** |

## Step 5: Test Error Handling

Create a corrupted HTML file to test error handling:

```bash
echo "<html><body>Broken" > test-html/broken.html
npm run export:parallel -- --input-dir test-html --output-dir test-output
```

Expected behavior:
- Other files export successfully
- Error summary shows `broken.html` failed
- Exit code remains 0 (partial success)

## Cleanup

```bash
rm -rf test-html test-output exports
```

```powershell
Remove-Item -Recurse -Force test-html, test-output, exports
```

## Troubleshooting

### "No browser executable found"

`browser.js` searches the usual Chrome/Edge/Chromium locations for your
platform. To point at a specific binary, set `CHROME_PATH`:

```bash
export CHROME_PATH="/path/to/chrome"
```

Alternatively install one through Playwright: `npx playwright install chromium`.

### "Input directory does not exist"

Ensure the path is absolute or relative to the current working directory:

```bash
# Use absolute path
npm run export:parallel -- --input-dir "$(pwd)/test-html" --output-dir "$(pwd)/test-output"

# Or cd to the parent directory first
cd ..
npm run export:parallel -- --input-dir ./html --output-dir ./画面
```

### Low Memory / Browser Crashes

Reduce concurrency:

```bash
npm run export:parallel -- --input-dir test-html --output-dir test-output --concurrency 1
```

## Advanced: Test with GSAP Animations

Create a test file with GSAP animation:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      margin: 0;
      padding: 0;
      width: 1080px;
      height: 1920px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Arial', sans-serif;
      background: #1a1a2e;
      color: #eee;
    }
    h1 {
      font-size: 120px;
      opacity: 0;
      transform: translateY(100px);
    }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
</head>
<body data-animation-duration="2000">
  <h1>Animated Text</h1>
  <script>
    // total duration: 2000
    gsap.to("h1", { 
      opacity: 1, 
      y: 0, 
      duration: 1.5,
      onComplete: () => {
        // Signal animation complete
        window.gsapAnimationComplete = Promise.resolve();
      }
    });
  </script>
</body>
</html>
```

The parallel exporter will:
1. Detect GSAP via `window.gsap` or `window.gsapAnimationComplete`
2. Wait for the animation to complete
3. Capture the final state
