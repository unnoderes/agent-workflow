# Agent Workflow

Agent-driven short video production workflow for educational and promotional content.

## Overview

This project automates the creation of short-form videos from segmented scripts, producing:
- **HTML frame previews** (one file per scene)
- **Cover images** (multiple aspect ratios)
- **TTS audio** with synchronized **SRT subtitles** (via MiniMax API)
- **PNG exports** ready for editing software
- **Final MP4** assembled by FFmpeg (frames + audio + subtitles)

## Pipeline

```
Video theme/title
       ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Materials Collection (Notion)                 │
└─────────────────────────────────────────────────────────┘
       ↓
collect-video-materials → Notion workspace created
       ↓                  (Materials library + Script placeholder)
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Script Generation (Notion)                    │
└─────────────────────────────────────────────────────────┘
       ↓
generate-video-script → Full script written to Notion
       ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: Local Production                              │
└─────────────────────────────────────────────────────────┘
       ↓
init-video-project → Create project directory from template
       ↓
Segmented script
       ↓
       ├─→ short-video-frames → HTML frames (frame_01.html … frame_N.html)
       ├─→ short-video-cover   → Cover HTML
       └─→ tts-video           → MP3 audio + SRT subtitles
                ↓
       html-image-export → PNG exports (Playwright)
                ↓
       画面/*.png + 封面/cover.png
                ↓
       assemble-video → final_output.mp4 (FFmpeg)
```

The three generation steps (frames, cover, TTS) are **independent and can run in parallel** once style parameters are confirmed. `assemble-video` runs last.

## Skills

| Skill | Purpose |
|-------|---------|
| `collect-video-materials` | **Phase 1**: Create Notion workspace, web search for materials (hooks, data, cases), write to Notion materials library |
| `generate-video-script` | **Phase 2**: Read Notion materials, analyze coverage, optional supplement search, design structure, generate segmented script with parameters, write to Notion |
| `init-video-project` | **Phase 3**: Initialize project directory from Desktop template |
| `short-video-frames` | Convert segmented script into per-frame HTML previews |
| `short-video-cover` | Generate cover HTML for the video |
| `tts-video` | Call MiniMax TTS to produce MP3 audio and SRT subtitles |
| `html-image-export` | Render local HTML files to stable PNG exports via Playwright |
| `assemble-video` | Join PNG frames + MP3 + SRT into the final MP4 via FFmpeg (hard/soft/no subtitles) |
| `agents-layout` | *(General-purpose)* Decompose a dev task into multi-agent layout |

## Requirements

| Dependency | Required by |
|------------|-------------|
| **Notion MCP Server** | `collect-video-materials`, `generate-video-script` |
| Python 3 | `tts-video` (script parsing, SRT generation), `assemble-video` |
| `mutagen` or `ffprobe` | `tts-video` (audio duration reading) |
| `ffmpeg` + `ffprobe` | `tts-video` (audio merging), `assemble-video` (encoding; hard subtitles need libass) |
| Node.js + `playwright-core` | `html-image-export` |
| MiniMax API key | `tts-video` |

## Setup

1. **Set MiniMax API key** as environment variable:
   ```bash
   export MINIMAX_API_KEY="sk-api-..."
   ```

2. **Connect Notion MCP Server** in Claude Code:
   - Install and configure the Notion MCP server
   - Authenticate with your Notion workspace
   - Required for `collect-video-materials` and `generate-video-script`

3. **Prepare Desktop template** (required by `init-video-project`):
   ```
   ~/Desktop/directory-template/
   ├── html/
   ├── 画面/
   ├── 封面/
   ├── 音频/
   └── 字幕/
   ```

4. **Install Python dependencies** (optional, for `tts-video`):
   ```bash
   pip install mutagen
   ```

5. **Install Playwright** (for `html-image-export`):
   ```bash
   cd html-image-export/assets/exporter-project
   npm install
   ```

6. **(Optional) Create template directory**:
   ```bash
   # Bash
   ./scripts/ensure_directory_template.sh
   
   # PowerShell
   .\scripts\ensure_directory_template.ps1
   ```
   
   > **Note**: If the template directory doesn't exist on your Desktop, `init-video-project` will automatically create it on first use. This step is optional.

## Usage

### Quick Start

1. **Collect materials in Notion** (with web research):
   ```bash
   # AI agent will search the web, extract materials, create Notion workspace
   "Collect materials for video: [your topic]"
   ```

2. **Generate script from materials**:
   ```bash
   # AI agent will read materials, analyze coverage, generate full script
   "Generate script from workspace: [Notion URL]"
   ```

3. **Initialize local project**:
   ```bash
   "Run init-video-project for [project-name]"
   ```

4. **Generate video assets** (parallel):
   ```bash
   "Generate frames, cover, and audio from the script"
   ```

5. **Export and assemble**:
   ```bash
   # Parallel export HTML to PNG (recommended)
   "Export HTML to PNG using parallel mode"
   
   # Or manually execute
   cd html-image-export/assets/exporter-project
   npm run export:parallel -- --input-dir <project>/html --output-dir <project>/画面
   
   # Assemble the final video
   "Assemble the final video"
   ```

See `agents.md` for detailed pipeline documentation and shared parameters (aspect ratio, art style, TTS voice, etc.).

## Output Layout

```
<working-dir>/
  video-frames/
    frame_01.html
    frame_02.html
    …
    cover.html
    exports/
      frame_01.png
      frame_02.png
      …
      cover.png
  tts_output/
    segments/
      seg_001.mp3
      seg_002.mp3
      …
    final.mp3
    subtitles.srt
  final_output.mp4      ← assemble-video
  concat_list.txt       ← assemble-video (intermediate)
```

## Tests

`assemble-video` has a test suite covering SRT parsing, concat-manifest generation and a real FFmpeg end-to-end run (3 frames + 9 s audio, subtitle alignment within 50 ms):

```bash
python -m unittest discover -s scripts/tests
```

The end-to-end tests generate their fixtures with FFmpeg's `lavfi` sources, so no binary assets are committed. They skip automatically when `ffmpeg`/`ffprobe` are missing.

## Roadmap

- [x] Add final assembly step (FFmpeg: PNG sequence + audio + subtitles → MP4)
- [x] Precise audio-visual alignment using SRT timestamps
- [x] GSAP animation integration for in-frame element animations
- [x] Playwright video recording support (WebM format)
- [ ] Batch production script for multiple videos
- [ ] CI/CD integration for automated video generation

## License

MIT

## Archive Note

This project was archived from `llm-workspace-archive-2604261522` and initialized for version control on 2025-10-21. Original files dated 2026-04-19 to 2026-04-26.
