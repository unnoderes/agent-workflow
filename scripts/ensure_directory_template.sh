#!/bin/bash
# Ensure directory-template exists on Desktop

TEMPLATE_PATH="$HOME/Desktop/directory-template"

if [ -d "$TEMPLATE_PATH" ]; then
    echo "✓ Template directory already exists: $TEMPLATE_PATH"
    exit 0
fi

echo "ℹ️  Template directory not found. Creating standard structure..."

mkdir -p "$TEMPLATE_PATH/html"
mkdir -p "$TEMPLATE_PATH/画面"
mkdir -p "$TEMPLATE_PATH/封面"
mkdir -p "$TEMPLATE_PATH/音频"
mkdir -p "$TEMPLATE_PATH/字幕"

# Create README in template
cat > "$TEMPLATE_PATH/README.md" << 'README'
# Video Project Template

This is the standard directory structure for video projects.

## Structure

- `html/` - HTML source files (frames + cover)
- `画面/` - Exported frame images (PNG)
- `封面/` - Exported cover image (PNG)
- `音频/` - TTS audio files (MP3)
- `字幕/` - Subtitle files (SRT)

## Usage

This template is automatically copied by `init-video-project` skill.
Do not modify this template directly.
README

echo "✓ Template directory created successfully:"
echo "  $TEMPLATE_PATH"
echo "    ├── html/"
echo "    ├── 画面/"
echo "    ├── 封面/"
echo "    ├── 音频/"
echo "    └── 字幕/"
