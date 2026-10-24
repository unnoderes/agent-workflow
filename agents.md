# agents.md

This file is the canonical reference for any AI agent working in this project. Read it before invoking any skill or producing any output.

---

## Project

Short-video production workflow. Given a segmented video script, this project produces HTML frame previews, a cover image, TTS audio with SRT subtitles, final exported PNGs, and the assembled MP4 — ready for publishing.

---

## Skill Index

### Video Production Pipeline Skills

| File | Skill name | Role in pipeline |
|------|------------|-----------------|
| `.agents/skills/collect-video-materials/SKILL.md` | `collect-video-materials` | **Phase 1 (Materials).** Create Notion workspace, collect materials via web search, write structured materials to Notion |
| `.agents/skills/generate-video-script/SKILL.md` | `generate-video-script` | **Phase 2 (Script).** Read materials from Notion, analyze coverage, design structure, generate segmented script, recommend parameters, write back to Notion |
| `init-video-project.md` | `init-video-project` | **Phase 3 (Project Init).** Copy the Desktop template and create the project directory for a new video |
| `short-video-frames.md` | `short-video-frames` | Convert segmented script into per-frame HTML previews |
| `cover_skill.md` | `short-video-cover` | Generate a cover HTML for the video |
| `tts-video-skill.md` | `tts-video` | Call MiniMax TTS to produce MP3 audio and SRT subtitles |
| `html-image-export/SKILL.md` | `html-image-export` | Render local HTML files to stable PNG exports or animated WebM videos via Playwright (supports GSAP animations) |
| `.claude/commands/assemble-video.md` | `assemble-video` | **Run last.** Join PNG frames + MP3 + SRT into the final MP4 via FFmpeg |
| `agents-layout.backup.md` | `agents-layout` | *(General-purpose)* Decompose a dev task into a multi-agent layout with ready-to-paste prompts |

> `agents-layout` is a general-purpose orchestration skill. It is not part of the video pipeline.

`assemble-video` ships its tooling as scripts under `scripts/` (`assemble_video.py`, `generate_concat_list.py`, `parse_srt_durations.py`); its tests live in `scripts/tests/`.

---

## Pipeline

```
Video theme / title
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 1: Materials Collection (Notion-based)            │
└──────────────────────────────────────────────────────────┘
       │
       ▼
collect-video-materials  ──► Notion Workspace
       │                        ├─ 📚 Materials Library
       │                        ├─ 📝 Script (placeholder)
       │                        └─ 🎬 Project Info
       │
       ├── Web search 3+ times
       ├── Extract hooks, data, cases, comparisons
       └── Write to Notion Materials Library
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 2: Script Generation (Notion-based)               │
└──────────────────────────────────────────────────────────┘
       │
       ▼
generate-video-script  ──► Read Materials Library
       │                   ├─ Analyze coverage
       │                   ├─ Optional: supplement search
       │                   ├─ Design structure
       │                   ├─ Generate segmented script
       │                   └─ Recommend parameters
       │
       └───► Write back to Notion Script Page
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 3: Local Project Setup                            │
└──────────────────────────────────────────────────────────┘
       │
       ▼
init-video-project  ──► <project-dir>/  (.agent/skills, html, 画面, 封面, 音频, 字幕)
       │
   Segmented script (from Notion or manual)
       │
       ├──► short-video-frames ──► <project-dir>/html/frame_01.html … frame_N.html
       │
       ├──► short-video-cover  ──► <project-dir>/html/cover.html
       │
       └──► tts-video          ──► <project-dir>/音频/final.mp3
                                   <project-dir>/字幕/subtitles.srt
                                          │
                                          ▼
                               html-image-export
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                  <project-dir>/画面/*.png   <project-dir>/封面/cover.png
                              │
                              ▼
                  assemble-video  (+ 音频/final.mp3 + 字幕/subtitles.srt)
                              │
                              ▼
                  <project-dir>/final_output.mp4
                  <project-dir>/concat_list.txt
```

The three generation steps (frames, cover, TTS) have no dependency on each other and can run in parallel once style parameters are confirmed. `assemble-video` runs last: it needs the exported frames **and** the TTS audio + subtitles.

---

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
    subtitles.srt
  final_output.mp4      ← assemble-video
  concat_list.txt       ← assemble-video (intermediate, regenerable)
```

---

## Shared Parameters

The following parameters are determined once per session during Phase 1 of any pipeline skill. All subsequent skills reuse the confirmed values without asking again.

| Parameter | Options |
|-----------|---------|
| **Aspect ratio** | A · 16:9 / B · 9:16 / C · 1:1 (frames) or A · 16:9 / B · 3:4 / C · 9:16 (cover) |
| **Art style** | 1 · Minimal white / 2 · Dark tech / 3 · Warm parchment / 4 · Magazine contrast / 5 · Custom |
| **TTS voice** | `voice_id` string (default: `Chinese_deep_voiced_male_vv1`) |
| **TTS speed** | Float 0.5–2.0 (default: `1.2`) |

---

## Conventions

**HTML output**
- One file per frame. Never merge frames into a single-page app.
- Fixed width/height matching the selected aspect ratio.
- Fully self-contained. External fonts via Google Fonts CDN only.
- No local-path `<img>`. Use SVG, CSS shapes, or Unicode characters instead.
- First line must be a comment: `<!-- Frame N | [keyword] | [style code] -->` or `<!-- Cover | … -->`.

**Export**
- PNG export is always triggered explicitly by the user. No skill auto-exports.
- Exports go to `exports/` inside the HTML source directory.
- Use `html-image-export` for any HTML-to-PNG conversion; do not use ad-hoc screenshot commands.

**TTS**
- Preview the first segment before batch-generating. Skip preview only if the user explicitly says so.
- Insert 300 ms silence between segments when merging audio.
- Segment files: `seg_001.mp3`, `seg_002.mp3`, … (zero-padded, three digits).

**Assembly**
- One frame per subtitle cue. The N-th cue's duration is the N-th frame's on-screen time; a frame/segment count mismatch is an error, never a guess.
- Frames must share one size with even width and height (`yuv420p` cannot encode odd dimensions).
- Subtitles must be UTF-8; the SRT is both the burn-in source and the timeline source.
- Default output is H.264 + AAC 192 kbps `yuv420p`, hard subtitles burned in.
- Never overwrite an existing `final_output.mp4` without confirming with the user (the script requires `--force`).
- `concat_list.txt` is an intermediate artifact: safe to delete, regenerated on every run.

**General**
- Never overwrite existing HTML frames without confirming with the user.
- Manual-screenshot frames (real GitHub UI, live demos, third-party logos) are noted in the output checklist but no HTML placeholder is generated.
- `html-image-export` handles CSS animations correctly; prefer it over any simpler screenshot method.

---

## Environment Dependencies

| Dependency | Required by |
|------------|-------------|
| Python 3 | `tts-video` (script parsing, SRT generation), `assemble-video` (timeline + FFmpeg orchestration) |
| `mutagen` or `ffprobe` | `tts-video` (audio duration reading) |
| `ffmpeg` + `ffprobe` | `tts-video` (audio merging), `assemble-video` (encoding). Hard subtitles additionally need an FFmpeg build with libass |
| Node.js + `playwright-core` | `html-image-export` |
| Network — Google Fonts CDN | `short-video-frames`, `short-video-cover` |
| Network — MiniMax API | `tts-video` |
| Desktop template directory | `init-video-project` (auto-created if missing via `scripts/ensure_directory_template.{sh,ps1}`) |
