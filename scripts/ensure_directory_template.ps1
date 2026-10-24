# Ensure directory-template exists on Desktop
param(
    [string]$TemplatePath = "$env:USERPROFILE\Desktop\directory-template"
)

if (Test-Path $TemplatePath) {
    Write-Host "✓ Template directory already exists: $TemplatePath" -ForegroundColor Green
    exit 0
}

Write-Host "ℹ️  Template directory not found. Creating standard structure..." -ForegroundColor Yellow

# Create directory structure
New-Item -Path "$TemplatePath\html" -ItemType Directory -Force | Out-Null
New-Item -Path "$TemplatePath\画面" -ItemType Directory -Force | Out-Null
New-Item -Path "$TemplatePath\封面" -ItemType Directory -Force | Out-Null
New-Item -Path "$TemplatePath\音频" -ItemType Directory -Force | Out-Null
New-Item -Path "$TemplatePath\字幕" -ItemType Directory -Force | Out-Null

# Create README in template
$readmeContent = @"
# Video Project Template

This is the standard directory structure for video projects.

## Structure

- ``html/`` - HTML source files (frames + cover)
- ``画面/`` - Exported frame images (PNG)
- ``封面/`` - Exported cover image (PNG)
- ``音频/`` - TTS audio files (MP3)
- ``字幕/`` - Subtitle files (SRT)

## Usage

This template is automatically copied by ``init-video-project`` skill.
Do not modify this template directly.
"@

Set-Content -Path "$TemplatePath\README.md" -Value $readmeContent -Encoding UTF8

Write-Host "✓ Template directory created successfully:" -ForegroundColor Green
Write-Host "  $TemplatePath"
Write-Host "    ├── html/"
Write-Host "    ├── 画面/"
Write-Host "    ├── 封面/"
Write-Host "    ├── 音频/"
Write-Host "    └── 字幕/"
