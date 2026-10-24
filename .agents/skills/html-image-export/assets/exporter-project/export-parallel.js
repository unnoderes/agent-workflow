const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright-core");
const { launchOptions } = require("./browser");

// Parse command-line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    inputDir: null,
    outputDir: null,
    concurrency: 3,
    include: "*.html",
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--input-dir" && i + 1 < args.length) {
      config.inputDir = args[++i];
    } else if (args[i] === "--output-dir" && i + 1 < args.length) {
      config.outputDir = args[++i];
    } else if (args[i] === "--concurrency" && i + 1 < args.length) {
      config.concurrency = parseInt(args[++i], 10);
    } else if (args[i] === "--include" && i + 1 < args.length) {
      config.include = args[++i];
    }
  }

  return config;
}

/**
 * Build a filename filter from a comma-separated list of `*` / `?` patterns.
 *
 * Frames and the cover usually share one source directory but export into
 * different output directories, so the caller selects which files a run picks
 * up: `--include "frame_*.html"` versus `--include cover.html`.
 */
function compileInclude(spec) {
  const patterns = spec
    .split(",")
    .map((pattern) => pattern.trim())
    .filter(Boolean);

  if (patterns.length === 0) {
    return () => true;
  }

  const sources = patterns.map((pattern) =>
    pattern
      .replace(/[.+^${}()|[\]\\]/g, "\\$&")
      .replace(/\*/g, "[^/]*")
      .replace(/\?/g, "[^/]")
  );
  const regex = new RegExp(`^(?:${sources.join("|")})$`, "i");
  return (fileName) => regex.test(fileName);
}

// Scan input directory for HTML files matching the include patterns
function scanHtmlFiles(dir, include) {
  if (!fs.existsSync(dir)) {
    throw new Error(`Input directory does not exist: ${dir}`);
  }

  const files = fs
    .readdirSync(dir)
    .filter((name) => name.toLowerCase().endsWith(".html"))
    .filter(include)
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
async function exportParallel(inputDir, outputDir, concurrency, include) {
  const htmlFiles = scanHtmlFiles(inputDir, include);

  if (htmlFiles.length === 0) {
    throw new Error(`No HTML files matching the include patterns were found in: ${inputDir}`);
  }

  console.log(`Found ${htmlFiles.length} HTML file(s)`);
  console.log(`Using ${concurrency} concurrent browser(s)\n`);

  // Create output directory
  fs.mkdirSync(outputDir, { recursive: true });

  // Launch N browser instances
  const browsers = await Promise.all(
    Array(concurrency)
      .fill()
      .map(() => chromium.launch(launchOptions()))
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
    console.error(
      "  node export-parallel.js --input-dir <path> --output-dir <path> [--concurrency N] [--include \"<pattern,...>\"]"
    );
    console.error("\nExamples:");
    console.error("  node export-parallel.js --input-dir ./html --output-dir ./画面 --include \"frame_*.html\"");
    console.error("  node export-parallel.js --input-dir ./html --output-dir ./封面 --include cover.html");
    process.exit(1);
  }

  if (!config.outputDir) {
    console.error("Error: --output-dir is required");
    console.error("\nUsage:");
    console.error(
      "  node export-parallel.js --input-dir <path> --output-dir <path> [--concurrency N] [--include \"<pattern,...>\"]"
    );
    process.exit(1);
  }

  if (!Number.isInteger(config.concurrency) || config.concurrency < 1) {
    console.error("Error: --concurrency must be an integer >= 1");
    process.exit(1);
  }

  console.log(`Input directory: ${config.inputDir}`);
  console.log(`Output directory: ${config.outputDir}`);
  console.log(`Include: ${config.include}`);
  console.log(`Concurrency: ${config.concurrency}\n`);

  await exportParallel(
    config.inputDir,
    config.outputDir,
    config.concurrency,
    compileInclude(config.include)
  );
}

main().catch((error) => {
  console.error("\nFatal error:", error.message);
  process.exit(1);
});
