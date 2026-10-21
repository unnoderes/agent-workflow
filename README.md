# Agent Workflow

Agent-driven short video production workflow for educational and promotional content.

## Overview

This project automates the creation of short-form videos from segmented scripts, producing:
- **HTML frame previews** (one file per scene)
- **Cover images** (multiple aspect ratios)
- **TTS audio** with synchronized **SRT subtitles** (via MiniMax API)
- **PNG exports** ready for editing software

## Pipeline

```
Video theme/title
       ↓
init-video-project  → Create project directory from template
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
```

The three generation steps (frames, cover, TTS) are **independent and can run in parallel** once style parameters are confirmed.

## Skills

| Skill | Purpose |
|-------|---------|
| `init-video-project` | Initialize project directory from Desktop template |
| `short-video-frames` | Convert segmented script into per-frame HTML previews |
| `short-video-cover` | Generate cover HTML for the video |
| `tts-video` | Call MiniMax TTS to produce MP3 audio and SRT subtitles |
| `html-image-export` | Render local HTML files to stable PNG exports via Playwright |
| `agents-layout` | *(General-purpose)* Decompose a dev task into multi-agent layout |

## Requirements

| Dependency | Required by |
|------------|-------------|
| Python 3 | `tts-video` (script parsing, SRT generation) |
| `mutagen` or `ffprobe` | `tts-video` (audio duration reading) |
| `ffmpeg` | `tts-video` (audio merging) |
| Node.js + `playwright-core` | `html-image-export` |
| MiniMax API key | `tts-video` |

## Setup

1. **Set MiniMax API key** as environment variable:
   ```bash
   export MINIMAX_API_KEY="sk-api-..."
   ```

2. **Prepare Desktop template** (required by `init-video-project`):
   ```
   ~/Desktop/directory-template/
   ├── html/
   ├── 画面/
   ├── 封面/
   ├── 音频/
   └── 字幕/
   ```

3. **Install Python dependencies** (optional, for `tts-video`):
   ```bash
   pip install mutagen
   ```

4. **Install Playwright** (for `html-image-export`):
   ```bash
   cd html-image-export/assets/exporter-project
   npm install
   ```

## Usage

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
```

## Roadmap

- [ ] Add final assembly step (FFmpeg: PNG sequence + audio + subtitles → MP4)
- [ ] Precise audio-visual alignment using SRT timestamps
- [ ] Batch production script for multiple videos
- [ ] CI/CD integration for automated video generation

## License

MIT

## Archive Note

This project was archived from `llm-workspace-archive-2604261522` and initialized for version control on 2025-10-21. Original files dated 2026-04-19 to 2026-04-26.
