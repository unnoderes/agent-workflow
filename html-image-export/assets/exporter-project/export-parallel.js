const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright-core");

// Parse command-line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    inputDir: null,
    outputDir: null,
    concurrency: 3,
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--input-dir" && i + 1 < args.length) {
      config.inputDir = args[++i];
    } else if (args[i] === "--output-dir" && i + 1 < args.length) {
      config.outputDir = args[++i];
    } else if (args[i] === "--concurrency" && i + 1 < args.length) {
      config.concurrency = parseInt(args[++i], 10);
    }
  }

  return config;
}

// Browser path discovery (Windows)
const browserCandidates = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];

function getBrowserPath() {
  const browserPath = browserCandidates.find((candidate) => fs.existsSync(candidate));
  if (!browserPath) {
    throw new Error("No Chrome/Edge executable found.");
  }
  return browserPath;
}

// Scan input directory for HTML files
function scanHtmlFiles(dir) {
  if (!fs.existsSync(dir)) {
    throw new Error(`Input directory does not exist: ${dir}`);
  }

  const files = fs
    .readdirSync(dir)
    .filter((name) => name.toLowerCase().endsWith(".html"))
    .sort((a, b) => a.localeCompare(b));

  return files;
}

// Infer viewport dimensions from HTML content
function inferViewport(html) {
  const widthMatch = html.match(/width:\s*(\d+)px/);
  const heightMatch = html.match(/height:\s*(\d+)px/);
  const width = widthMatch ? Number(widthMatch[1]) : 1920;
  const height = heightMatch ? Number(heightMatch[1]) : 1080;
  return { width, height };
}

// Infer animation duration from HTML content
function inferAnimationDuration(html) {
  // Check for explicit duration attribute
  const durationMatch = html.match(/data-animation-duration=["'](\d+)["']/);
  if (durationMatch) {
    return Number(durationMatch[1]);
  }

  // Check for GSAP duration comment
  const gsapMatch = html.match(/\/\/\s*total duration:\s*(\d+)/);
  if (gsapMatch) {
    return Number(gsapMatch[1]);
  }

  // Default to 3 seconds
  return 3000;
}

// Settle page: wait for fonts, finish animations, force final states
async function settlePage(page, html) {
  const animationDuration = inferAnimationDuration(html);

  await page.evaluate(async () => {
    // Wait for fonts to load
    if (document.fonts && document.fonts.ready) {
      try {
        await document.fonts.ready;
      } catch {}
    }

    // Wait for initial render
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });

  // Check if page has GSAP animations
  const hasGsap = await page.evaluate(() => {
    return typeof window.gsap !== "undefined" || window.gsapAnimationComplete !== undefined;
  });

  if (hasGsap) {
    // Wait for GSAP animation complete signal or timeout
    await Promise.race([
      page.evaluate(() => {
        if (window.gsapAnimationComplete) {
          return window.gsapAnimationComplete;
        }
        return new Promise(() => {}); // Never resolves
      }),
      page.waitForTimeout(animationDuration + 1000),
    ]).catch(() => {});
  } else {
    // Handle CSS animations
    await page.evaluate(async () => {
      // Finish all CSS animations
      for (const animation of document.getAnimations()) {
        try {
          animation.finish();
        } catch {
          try {
            animation.cancel();
          } catch {}
        }
      }

      // Force final states for hidden elements
      for (const element of document.querySelectorAll("*")) {
        const style = window.getComputedStyle(element);
        if (style.opacity === "0") {
          element.style.opacity = "1";
        }
        if (style.transform && style.transform !== "none") {
          element.style.transform = "none";
        }
      }

      // Wait for final render
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
  }
}

// Export a single HTML file to PNG
async function exportFile(browser, inputDir, outputDir, fileName) {
  const filePath = path.join(inputDir, fileName);
  const html = fs.readFileSync(filePath, "utf8");
  const viewport = inferViewport(html);

  const page = await browser.newPage({
    viewport,
    deviceScaleFactor: 1,
  });

  try {
    await page.goto(pathToFileURL(filePath).href, { waitUntil: "load" });
    await settlePage(page, html);

    const outputFileName = `${path.parse(fileName).name}.png`;
    const outputPath = path.join(outputDir, outputFileName);

    await page.screenshot({
      path: outputPath,
      clip: { x: 0, y: 0, width: viewport.width, height: viewport.height },
      type: "png",
    });

    return { success: true, fileName };
  } catch (error) {
    return { success: false, fileName, error: error.message };
  } finally {
    await page.close();
  }
}

// Process files assigned to a single browser instance
async function processBatch(browser, tasks, inputDir, outputDir, browserIndex) {
  const results = [];

  for (const task of tasks) {
    const result = await exportFile(browser, inputDir, outputDir, task.fileName);
    results.push(result);

    if (result.success) {
      console.log(`[Browser ${browserIndex + 1}] Exported ${result.fileName}`);
    } else {
      console.error(`[Browser ${browserIndex + 1}] Failed ${result.fileName}: ${result.error}`);
    }
  }

  return results;
}

// Main parallel export function
async function exportParallel(inputDir, outputDir, concurrency) {
  const htmlFiles = scanHtmlFiles(inputDir);

  if (htmlFiles.length === 0) {
    throw new Error(`No HTML files found in: ${inputDir}`);
  }

  console.log(`Found ${htmlFiles.length} HTML file(s)`);
  console.log(`Using ${concurrency} concurrent browser(s)\n`);

  // Create output directory
  fs.mkdirSync(outputDir, { recursive: true });

  // Get browser path
  const executablePath = getBrowserPath();

  // Launch N browser instances
  const browsers = await Promise.all(
    Array(concurrency)
      .fill()
      .map(() =>
        chromium.launch({
          headless: true,
          executablePath,
        })
      )
  );

  try {
    // Distribute files across browsers (round-robin)
    const tasks = htmlFiles.map((fileName, index) => ({
      fileName,
      browserIndex: index % concurrency,
    }));

    // Group tasks by browser
    const tasksByBrowser = Array(concurrency)
      .fill()
      .map(() => []);

    for (const task of tasks) {
      tasksByBrowser[task.browserIndex].push(task);
    }

    // Process all batches in parallel
    const startTime = Date.now();

    const allResults = await Promise.all(
      browsers.map((browser, index) =>
        processBatch(browser, tasksByBrowser[index], inputDir, outputDir, index)
      )
    );

    const endTime = Date.now();
    const elapsedSeconds = ((endTime - startTime) / 1000).toFixed(1);

    // Flatten results and generate summary
    const results = allResults.flat();
    const successCount = results.filter((r) => r.success).length;
    const failureCount = results.filter((r) => !r.success).length;

    console.log(`\n${'='.repeat(60)}`);
    console.log(`Export complete: ${successCount}/${htmlFiles.length} succeeded`);
    console.log(`Elapsed time: ${elapsedSeconds}s`);

    if (failureCount > 0) {
      console.log(`\nFailed files (${failureCount}):`);
      results
        .filter((r) => !r.success)
        .forEach((r) => {
          console.log(`  - ${r.fileName}: ${r.error}`);
        });
    }

    console.log(`\nOutput directory: ${outputDir}`);

    return results;
  } finally {
    // Close all browsers
    await Promise.all(browsers.map((b) => b.close()));
  }
}

// Entry point
async function main() {
  const config = parseArgs();

  if (!config.inputDir) {
    console.error("Error: --input-dir is required");
    console.error("\nUsage:");
    console.error("  node export-parallel.js --input-dir <path> --output-dir <path> [--concurrency N]");
    console.error("\nExample:");
    console.error("  node export-parallel.js --input-dir ./html --output-dir ./exports --concurrency 3");
    process.exit(1);
  }

  if (!config.outputDir) {
    console.error("Error: --output-dir is required");
    console.error("\nUsage:");
    console.error("  node export-parallel.js --input-dir <path> --output-dir <path> [--concurrency N]");
    process.exit(1);
  }

  if (config.concurrency < 1) {
    console.error("Error: --concurrency must be >= 1");
    process.exit(1);
  }

  console.log(`Input directory: ${config.inputDir}`);
  console.log(`Output directory: ${config.outputDir}`);
  console.log(`Concurrency: ${config.concurrency}\n`);

  await exportParallel(config.inputDir, config.outputDir, config.concurrency);
}

main().catch((error) => {
  console.error("\nFatal error:", error.message);
  process.exit(1);
});
