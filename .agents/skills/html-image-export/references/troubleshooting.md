# Troubleshooting

## Missing content in exported images

1. Verify the page is a standalone local HTML file and not a partial fragment.
2. Open the generated `export-screenshots.js` in the target directory and inspect the page-specific CSS or JS behavior.
3. If content is hidden by custom JavaScript instead of CSS animation, extend the script with an additional `page.evaluate(...)` block to reveal those nodes before screenshot.
4. If the page needs extra time to finish layout, add an explicit delay before screenshot or wait for a specific selector.

## Browser not found

The exporter looks for an installed Chromium-based browser, per platform:

- **Windows**: Chrome or Edge under `C:\Program Files[ (x86)]`
- **macOS**: Chrome, Edge, Chromium or Brave under `/Applications`
- **Linux**: `google-chrome`, `chromium`, `chromium-browser` or `microsoft-edge` on `PATH` locations

`browser.js` holds the full list. If none is found it falls back to Playwright's
own resolution, so `npx playwright install chromium` also works. To point at a
specific binary, set `CHROME_PATH`:

```bash
export CHROME_PATH="/opt/google/chrome/chrome"
```

## Wrong image size

The exporter infers viewport size from the first `width: <n>px` and `height: <n>px` values found in the HTML. If a file uses a more complex layout, patch `inferViewport` for that project or hardcode the expected dimensions.
