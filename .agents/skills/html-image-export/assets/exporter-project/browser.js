// Locate a Chromium-based browser to drive.
//
// `playwright-core` deliberately ships no browser, so something has to be
// found on the machine. Set CHROME_PATH to override the search; otherwise the
// per-platform list below is checked and, failing that, Playwright's own
// resolution is used (which covers `npx playwright install chromium`).

const fs = require("fs");

const CANDIDATES = {
  win32: [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ],
  darwin: [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ],
  linux: [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/microsoft-edge",
    "/snap/bin/chromium",
  ],
};

/** Path of a browser executable, or null to let Playwright resolve its own. */
function resolveBrowserPath() {
  if (process.env.CHROME_PATH) {
    return process.env.CHROME_PATH;
  }
  const candidates = CANDIDATES[process.platform] || [];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

/** Options for `chromium.launch()`, with `executablePath` only when found. */
function launchOptions(overrides = {}) {
  const executablePath = resolveBrowserPath();
  return {
    headless: true,
    ...(executablePath ? { executablePath } : {}),
    ...overrides,
  };
}

module.exports = { resolveBrowserPath, launchOptions };
