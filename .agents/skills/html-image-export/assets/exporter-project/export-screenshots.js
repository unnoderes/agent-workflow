const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { chromium } = require("playwright-core");
const { launchOptions } = require("./browser");

const cwd = process.cwd();
const outputDir = path.join(cwd, "exports");
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

async function settlePage(page) {
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) {
      try {
        await document.fonts.ready;
      } catch {}
    }

    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));

    for (const animation of document.getAnimations()) {
      try {
        animation.finish();
      } catch {
        try {
          animation.cancel();
        } catch {}
      }
    }

    for (const element of document.querySelectorAll("*")) {
      const style = window.getComputedStyle(element);
      if (style.opacity === "0") {
        element.style.opacity = "1";
      }
      if (style.transform && style.transform !== "none") {
        element.style.transform = "none";
      }
    }

    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  });
}

async function main() {
  if (htmlFiles.length === 0) {
    throw new Error("No HTML files found in the current directory.");
  }

  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch(launchOptions());

  try {
    for (const fileName of htmlFiles) {
      const filePath = path.join(cwd, fileName);
      const html = fs.readFileSync(filePath, "utf8");
      const viewport = inferViewport(html);
      const page = await browser.newPage({
        viewport,
        deviceScaleFactor: 1,
      });

      await page.goto(pathToFileURL(filePath).href, { waitUntil: "load" });
      await settlePage(page);

      await page.screenshot({
        path: path.join(outputDir, `${path.parse(fileName).name}.png`),
        clip: { x: 0, y: 0, width: viewport.width, height: viewport.height },
        type: "png",
      });

      await page.close();
      console.log(`exported ${fileName}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
