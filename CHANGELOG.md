# Changelog

## [Unreleased] - One output layout, working batch export

### Changed — one output layout

`README.md`, `agents.md` and every pipeline skill now describe the project
directory created by `init-video-project`, and nothing else. Two layouts used to
coexist: the docs promised `video-frames/` + `tts_output/`, while
`init-video-project` created `html/ 画面/ 封面/ 音频/ 字幕/` and
`assemble_video.py` hardcoded `画面/`, `音频/final.mp3`, `字幕/subtitles.srt` in
`PROJECT_DIRS`. The skills each had their own default (`./video-frames/`,
`~/tts_output`) that only an override table in `init-video-project` reconciled.

The project directory is now the single layout because that is what the tested
assembly engine enforces:

```
<project-dir>/
  html/     frame_01.html … frame_N.html, cover.html
  画面/     frame_01.png … frame_N.png
  封面/     cover.png
  音频/     final.mp3, segments/
  字幕/     subtitles.srt
```

- `init-video-project/SKILL.md`: the 路径映射 override table became a「项目目录结构」section that states where each skill writes.
- `short-video-frames`, `short-video-cover`, `tts-video`: the `./video-frames/`
  and `~/tts_output/` defaults are gone; they write into the project directory.
- `README.md`, `agents.md`: Output Layout redrawn; the Export convention no
  longer says "exports go to `exports/` inside the HTML source directory".

### Fixed — `bootstrap-exporter.ps1`

- **`export-parallel.js` was never copied.** `package.json` declares
  `export:parallel` and `SKILL.md` calls it the batch default, but the copy list
  omitted the file, so `npm run export:parallel` in a bootstrapped directory
  failed with MODULE_NOT_FOUND. The script now copies the whole exporter
  project (`package.json`, `browser.js`, and all three entry points), and
  `-ExportVideos` only selects which one runs.
- **npm ran in the wrong directory.** `npm install` and `npm run` inherited the
  caller's working directory, so the documented invocation
  (`cd <skill-dir>/scripts; ./bootstrap-exporter.ps1 -TargetDir <html-dir>`)
  installed into `scripts/` and then scanned `scripts/` for HTML files. Both now
  run inside `-TargetDir` via `Push-Location`/`Pop-Location`.
- `scripts/package.json` removed: it existed only to satisfy that misplaced
  `npm install` and nothing references it.

### Added — `--include` on `export-parallel.js`

Frames and the cover share `<project-dir>/html/`, so a run scoped to the whole
directory wrote `cover.png` into `画面/` and left `封面/` empty. `--include`
takes a comma-separated list of `*` / `?` filename patterns (default `*.html`,
case-insensitive):

```bash
npm run export:parallel -- --input-dir <project>/html --output-dir <project>/画面 --include "frame_*.html"
npm run export:parallel -- --input-dir <project>/html --output-dir <project>/封面 --include cover.html
```

A pattern that matches nothing exits 1 instead of silently exporting nothing.

### Added — `browser.js`

Browser discovery was four hardcoded `C:\Program Files\...` paths repeated in
three scripts, so macOS and Linux threw "No Chrome/Edge executable found" no
matter what was installed. `assets/exporter-project/browser.js` now resolves a
Chromium-based executable per platform (Windows, macOS, Linux), honours a
`CHROME_PATH` override, and returns `null` when nothing matches so Playwright's
own resolution covers `npx playwright install chromium`. The three entry
scripts and the docs that described patching `browserCandidates` all point at
it.

### Verified
- End-to-end on a scratch project: 2 frames + 1 cover exported into `画面/` and
  `封面/` respectively, then `scripts/assemble_video.py` produced a 6 s
  1080×1920 H.264/AAC MP4 with burned-in subtitles.
- `--include`: single pattern, comma list, `?` wildcard, case-insensitive
  match, and the no-match error path.
- `bootstrap-exporter.ps1` from the documented cwd: installs into the target
  directory, exports there, and `npm run export:parallel` works in the target.
- `python -m unittest discover -s scripts/tests` → 54 tests pass.

---

## [Unreleased] - Single source of truth for skills

Every skill now lives at exactly one path: `.agents/skills/<skill-name>/SKILL.md`.
Previously the same skills were maintained as five parallel copies
(`.agents/skills/`, `.claude/commands/`, `.claude/skills/` + `.skill` zips,
`.factory/skills/`, and loose `.md` files at the repository root) that had drifted
apart: the `.claude` and `.factory` copies predated GSAP support and parallel
export.

### Changed
- **`short-video-frames`, `short-video-cover`, `tts-video`, `init-video-project`,
  `agents-layout`** moved from loose root `.md` files into
  `.agents/skills/<name>/SKILL.md`. The root copies were the newest ones (they
  carried the GSAP and export-walkthrough sections) and are the ones kept.
- **`assemble-video`** moved from `.claude/commands/assemble-video.md` into
  `.agents/skills/assemble-video/SKILL.md`; it was previously defined only as a
  Claude Code slash command.
- **`html-image-export/`** moved wholesale to
  `.agents/skills/html-image-export/` so the skill and the exporter payload it
  copies into project directories travel together. `bootstrap-exporter.ps1`
  resolves the payload relative to its own location, so no script change was
  needed.
- Frontmatter normalised to the skill schema (`name` + `description`). The
  Claude Code-only fields `user-invocable` / `tools` and the `$ARGUMENTS`
  placeholders were replaced with plain instructions, so the same text works
  regardless of which agent loads it.
- `tts-video` step 4 gained the per-platform preview playback commands that
  existed only in the `.claude` copy; the "30 s silence counts as yes" default
  was dropped to match the existing rule that the preview must be confirmed.
- `init-video-project` no longer claims to copy a `.agent/skills/` directory
  into each project; skills are loaded from this repository, not duplicated per
  project.

### Removed
- `.claude/commands/` and `.claude/skills/` (stale duplicates)
- `.factory/skills/` (stale duplicates)
- `short-video-frames.skill`, `short-video-cover.skill` (zip packages of the
  pre-GSAP copies)

### Moved (not deleted)
- `video-script-planning` → `docs/archive/video-script-planning.md`. It was
  still discoverable as a skill while being marked deprecated in its own body.
- `html-image-export` parallel-export work reports
  (`CHANGES_SUMMARY.md`, `IMPLEMENTATION_REPORT.md`, `CHECKLIST.md`,
  `FINAL_REPORT.txt`) → `docs/archive/`, so the skill directory holds only the
  skill and its working files.
- `.agents/skills/QUICK_START.md` → `QUICK_START.md` at the repository root,
  beside `NOTION_WORKFLOW.md`.

### Fixed
- `agents.md` output layout listed `subtitles.srt` twice.
- Reference paths in `agents.md`, `README.md`, `QUICK_START.md` and inside the
  `html-image-export` docs now point at the new locations.

### Verified
- `python -m unittest discover -s scripts/tests` → 54 tests pass.
- All relative Markdown links across the repository resolve.

---

## [Unreleased] - Parallel PNG export

### Added
- **`export-parallel.js`** (`html-image-export/assets/exporter-project/`)
  - Multi-browser concurrent PNG export via Playwright
  - Flags: `--input-dir`, `--output-dir`, `--concurrency` (default 3)
  - Round-robin task distribution, per-file error isolation, progress logging
  - Settles CSS animations and GSAP timelines before capture
- `export:parallel` npm script in `package.json`
- Reference docs under `html-image-export/assets/exporter-project/`:
  `README.md`, `QUICK_REFERENCE.md`, `TEST.md`, `ARCHITECTURE.md`, `PERFORMANCE_TEST.md`

### Changed
- `html-image-export/SKILL.md`: parallel mode documented as the batch default; serial mode retained for 1–2 files
- Root `README.md`: quick-start export step now uses parallel mode
- `agents.md`: Export conventions note parallel mode for batches

### Verified
- 6 frames (1080×1920, CSS animation) exported 6/6: 2.59 s wall clock at
  `--concurrency 3` vs 3.22 s at `--concurrency 1` on the same machine.
  Gains grow with render cost per file; static pages are dominated by browser startup.

---

## [2025-01-XX] - Notion-Based Two-Phase Workflow

### Added

#### New Skills
- **`collect-video-materials`** (`.agents/skills/collect-video-materials/SKILL.md`)
  - Phase 1: Materials collection with Notion workspace creation
  - Web search 3+ times for hooks, data, cases, comparisons
  - Structured materials written to Notion library
  - Returns Notion workspace URL for next phase

- **`generate-video-script`** (`.agents/skills/generate-video-script/SKILL.md`)
  - Phase 2: Script generation from Notion materials
  - Automatic coverage analysis and optional supplementary search (0-3 times)
  - Structure design and segmented script generation
  - Production parameter recommendations (ratio, style, TTS)
  - Full script written back to Notion

#### Documentation
- **`NOTION_WORKFLOW.md`**: Complete guide for the two-phase workflow
  - Usage examples
  - Best practices for materials library
  - Team collaboration scenarios
  - Troubleshooting guide

### Changed
- **Pipeline architecture**: Split materials collection and script generation into two independent phases
- **`agents.md`**: Updated skill index and pipeline diagram to reflect new workflow
- **`README.md`**: Updated quick start guide, skills table, and pipeline diagram

### Deprecated
- **`video-script-planning`**: Marked as deprecated in favor of the new two-phase approach
  - Original functionality split into `collect-video-materials` + `generate-video-script`
  - Legacy skill file preserved for reference with deprecation notice

### Benefits
- **Separation of concerns**: Materials collection and script generation are independent
- **Reviewable**: Human review/editing of materials in Notion between phases
- **Reusable**: One materials library can generate multiple script versions
- **Collaborative**: Multiple team members can edit materials in Notion simultaneously
- **Traceable**: All intermediate artifacts permanently stored in Notion

### Migration Guide

**Old workflow**:
```bash
"Create a 60-second video script about [topic]"
```

**New workflow**:
```bash
# Phase 1: Collect materials
"Collect materials for video: [topic]"
# → Returns Notion workspace URL

# Phase 2: Generate script
"Generate script from workspace: [Notion URL]"
# → Returns Notion script page URL
```

### Technical Details
- Notion MCP Server integration for page creation and content updates
- Smart search strategy: 0-3 supplementary searches based on materials coverage
- Structured Notion workspace: Main page + Materials library + Script placeholder
- Materials taxonomy: Hooks, Data, Cases, Comparisons, References

---

For detailed usage instructions, see [NOTION_WORKFLOW.md](NOTION_WORKFLOW.md).
