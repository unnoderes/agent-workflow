const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright-core");
const { launchOptions } = require("./browser");

const cwd = process.cwd();
const outputDir = path.join(cwd, "video-exports");
const htmlFiles = fs
  .readdirSync(cwd)
  .filter((name) => name.toLowerCase().endsWith(".html"))
  .sort((a, b) => a.localeCompare(b));

function inferViewport(html) {
  const widthMatch = html.match(/width:\s*(\d+)px/);
  const heightMatch = html.match(/height:\s*(\d+)px/);
  const width = widthMatch ? Number(widthMatch[1]) : 1920;
  const height = heightMatch ? Number(heightMatch[1]) : 1080;
  return { width, height };
}

function inferAnimationDuration(html) {
  // Try to find animation completion marker or duration hint
  const durationMatch = html.match(/data-animation-duration=["'](\d+)["']/);
  if (durationMatch) {
    return Number(durationMatch[1]);
  }
  
  // Check for GSAP timeline duration comments
  const gsapMatch = html.match(/\/\/\s*total duration:\s*(\d+)/);
  if (gsapMatch) {
    return Number(gsapMatch[1]);
  }
  
  // Default to 3 seconds
  return 3000;
}

async function waitForAnimationComplete(page, maxWaitMs) {
  // Wait for fonts to load
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) {
      try {
        await document.fonts.ready;
      } catch {}
    }
  });

  // Wait a frame for initial render
  await page.evaluate(() => 
    new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  );

  // Wait for animation completion marker
  const hasCompletionMarker = await page.evaluate(() => {
    return document.querySelector('.animation-complete') !== null ||
           document.body.hasAttribute('data-animation-duration');
  });

  if (hasCompletionMarker) {
    // Wait for the ready class to be added
    await page.waitForSelector('body.ready, .animation-complete.ready', {
      timeout: maxWaitMs,
      state: 'attached'
    }).catch(() => {
      console.warn('Animation completion marker not set within timeout, proceeding anyway');
    });
  } else {
    // No explicit marker, wait for the calculated duration
    await page.waitForTimeout(maxWaitMs);
  }

  // Wait one more frame to ensure final state is rendered
  await page.evaluate(() => 
    new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  );
}

async function main() {
  if (htmlFiles.length === 0) {
    throw new Error("No HTML files found in the current directory.");
  }

  fs.mkdirSync(outputDir, { recursive: true });
  for (const fileName of htmlFiles) {
    const filePath = path.join(cwd, fileName);
    const html = fs.readFileSync(filePath, "utf8");
    const viewport = inferViewport(html);
    const animationDuration = inferAnimationDuration(html);
    const outputName = path.parse(fileName).name;
    const videoDir = path.join(outputDir, outputName);
    
    // Create a temporary directory for this video
    fs.mkdirSync(videoDir, { recursive: true });
    
    const browser = await chromium.launch(launchOptions());

    try {
      const context = await browser.newContext({
        viewport,
        deviceScaleFactor: 1,
        recordVideo: {
          dir: videoDir,
          size: { width: viewport.width, height: viewport.height },
        },
      });

      const page = await context.newPage();
      await page.goto(pathToFileURL(filePath).href, { waitUntil: "load" });
      
      // Wait for animation to complete
      await waitForAnimationComplete(page, animationDuration + 1000);

      // Close context to save the video
      await context.close();
      
      // Find the generated video file and move it to the output directory
      const videoFiles = fs.readdirSync(videoDir).filter(f => f.endsWith('.webm'));
      if (videoFiles.length > 0) {
        const videoFile = videoFiles[0];
        const sourcePath = path.join(videoDir, videoFile);
        const destPath = path.join(outputDir, `${outputName}.webm`);
        fs.renameSync(sourcePath, destPath);
        fs.rmdirSync(videoDir, { recursive: true });
        console.log(`exported ${fileName} → ${outputName}.webm`);
      } else {
        console.error(`No video file generated for ${fileName}`);
      }
    } finally {
      await browser.close();
    }
  }

  console.log('\nAll videos exported to:', outputDir);
  console.log('Note: Videos are in WebM format. Use FFmpeg to convert to MP4 if needed:');
  console.log('  ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});