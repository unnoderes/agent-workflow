---
name: html-image-export
description: Export one or more local HTML files into static PNG images. Use when Codex needs to batch render HTML mockups, slides, posters, covers, or other visual pages to images, especially when the pages contain CSS animations, delayed reveals, or transitions that would make normal screenshots capture incomplete intermediate states.
---

# HTML Image Export

Use the bundled exporter project to render local `.html` files into stable `.png` outputs.

Prefer this skill when:
- The working directory contains standalone HTML pages that need image export.
- The pages use CSS `animation`, `transition`, delayed `opacity`, or transform-based entry effects.
- Normal screenshots would capture partially revealed content.

## Workflow

1. Confirm the target directory that contains the `.html` files.
2. Use `scripts/bootstrap-exporter.ps1` to deploy the bundled exporter project into that directory.
3. Let the script install `playwright-core` if needed.
4. Run the exporter and write images into an `exports/` subdirectory beside the source HTML files.
5. Spot-check a few generated images. If a page still renders incompletely, read [references/troubleshooting.md](references/troubleshooting.md).

## Command

Run the wrapper script:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>"
```

Optional flags:

```powershell
powershell -ExecutionPolicy Bypass -File "<skill-dir>\scripts\bootstrap-exporter.ps1" -TargetDir "<html-dir>" -InstallDeps -ForceProjectSync
```

- `-InstallDeps`: Force `npm install` even if `node_modules/playwright-core` already exists.
- `-ForceProjectSync`: Overwrite the bundled exporter files in the target directory with the current skill version.

## Tool Layer

- `assets/exporter-project/package.json`: Minimal Node project used for export.
- `assets/exporter-project/export-screenshots.js`: Browser automation script that waits for fonts, finishes animations, and forces invisible animation-start elements into their visible final state before taking screenshots.
- `scripts/bootstrap-exporter.ps1`: Copies or refreshes the tool project into the target directory, installs dependencies, and runs the export.

## Output

The exporter writes:
- `<target-dir>\exports\*.png`

The wrapper also places the reusable tool files in the target directory:
- `<target-dir>\package.json`
- `<target-dir>\export-screenshots.js`

Preserve existing user HTML files. Do not rewrite source pages just to disable animation unless troubleshooting proves the renderer cannot recover the final state at runtime.
