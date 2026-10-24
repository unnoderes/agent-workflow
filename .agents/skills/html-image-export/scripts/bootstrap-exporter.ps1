param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir,

    [switch]$InstallDeps,

    [switch]$ForceProjectSync,

    [switch]$ExportVideos
)

$ErrorActionPreference = "Stop"

$resolvedTarget = (Resolve-Path -LiteralPath $TargetDir).Path
$skillRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Join-Path $skillRoot "assets\exporter-project"

# Copy the whole exporter project so every `npm run export:*` entry point works
# in the target directory; -ExportVideos only selects which one runs.
$filesToSync = @(
    "package.json",
    "browser.js",
    "export-screenshots.js",
    "export-parallel.js",
    "export-videos.js"
)

foreach ($fileName in $filesToSync) {
    $sourcePath = Join-Path $projectRoot $fileName
    $targetPath = Join-Path $resolvedTarget $fileName

    if ($ForceProjectSync -or -not (Test-Path -LiteralPath $targetPath)) {
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    }
}

# npm has to run inside the target directory: node_modules belongs there, and
# the exporter scripts scan the current directory for HTML files.
Push-Location -LiteralPath $resolvedTarget
try {
    $playwrightCoreDir = Join-Path $resolvedTarget "node_modules\playwright-core"
    if ($InstallDeps -or -not (Test-Path -LiteralPath $playwrightCoreDir)) {
        Write-Host "Installing playwright-core in $resolvedTarget"
        npm install playwright-core | Out-Host
    }

    if ($ExportVideos) {
        Write-Host "Exporting HTML files as videos in $resolvedTarget"
        npm run export:videos | Out-Host
    } else {
        Write-Host "Exporting HTML files as screenshots in $resolvedTarget"
        npm run export:screenshots | Out-Host
    }
} finally {
    Pop-Location
}
