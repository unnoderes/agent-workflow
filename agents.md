# agents.md

This file is the canonical reference for any AI agent working in this project. Read it before invoking any skill or producing any output.

---

## Project

Short-video production workflow. Given a segmented video script, this project produces HTML frame previews, a cover image, TTS audio with SRT subtitles, and final exported PNGs — ready for editing and publishing.

---

## Skill Index

| File | Skill name | Role in pipeline |
|------|------------|-----------------|
| `init-video-project.md` | `init-video-project` | **Run first.** Copy the Desktop template and create the project directory for a new video |
| `short-video-frames.md` | `short-video-frames` | Convert segmented script into per-frame HTML previews |
| `cover_skill.md` | `short-video-cover` | Generate a cover HTML for the video |
| `tts-video-skill.md` | `tts-video` | Call MiniMax TTS to produce MP3 audio and SRT subtitles |
| `html-image-export/SKILL.md` | `html-image-export` | Render local HTML files to stable PNG exports via Playwright |
| `agents-layout.backup.md` | `agents-layout` | *(General-purpose)* Decompose a dev task into a multi-agent layout with ready-to-paste prompts |

> `agents-layout` is a general-purpose orchestration skill. It is not part of the video pipeline.

---

## Pipeline

```
Video theme / title
       │
       ▼
init-video-project  ──► <project-dir>/  (.agent/skills, html, 画面, 封面, 音频, 字幕)
       │
Segmented script
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
```

The three generation steps (frames, cover, TTS) have no dependency on each other and can run in parallel once style parameters are confirmed.

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

**General**
- Never overwrite existing HTML frames without confirming with the user.
- Manual-screenshot frames (real GitHub UI, live demos, third-party logos) are noted in the output checklist but no HTML placeholder is generated.
- `html-image-export` handles CSS animations correctly; prefer it over any simpler screenshot method.

---

## Environment Dependencies

| Dependency | Required by |
|------------|-------------|
| Python 3 | `tts-video` (script parsing, SRT generation) |
| `mutagen` or `ffprobe` | `tts-video` (audio duration reading) |
| `ffmpeg` | `tts-video` (audio merging) |
| Node.js + `playwright-core` | `html-image-export` |
| Network — Google Fonts CDN | `short-video-frames`, `short-video-cover` |
| Network — MiniMax API | `tts-video` |
