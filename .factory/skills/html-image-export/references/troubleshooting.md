# Troubleshooting

## Missing content in exported images

1. Verify the page is a standalone local HTML file and not a partial fragment.
2. Open the generated `export-screenshots.js` in the target directory and inspect the page-specific CSS or JS behavior.
3. If content is hidden by custom JavaScript instead of CSS animation, extend the script with an additional `page.evaluate(...)` block to reveal those nodes before screenshot.
4. If the page needs extra time to finish layout, add an explicit delay before screenshot or wait for a specific selector.

## Browser not found

The exporter looks for:
- `C:\Program Files\Google\Chrome\Application\chrome.exe`
- `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
- `C:\Program Files\Microsoft\Edge\Application\msedge.exe`
- `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`

If none exist, either install Chrome/Edge or patch `export-screenshots.js` to point at an available Chromium-based browser.

## Wrong image size

The exporter infers viewport size from the first `width: <n>px` and `height: <n>px` values found in the HTML. If a file uses a more complex layout, patch `inferViewport` for that project or hardcode the expected dimensions.
