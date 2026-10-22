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
$projectRoot = Join-Path $skillRoot "assets\\exporter-project"

$filesToSync = @(
    "package.json",
    "export-screenshots.js"
)

if ($ExportVideos) {
    $filesToSync += "export-videos.js"
}

foreach ($fileName in $filesToSync) {
    $sourcePath = Join-Path $projectRoot $fileName
    $targetPath = Join-Path $resolvedTarget $fileName

    if ($ForceProjectSync -or -not (Test-Path -LiteralPath $targetPath)) {
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    }
}

$playwrightCoreDir = Join-Path $resolvedTarget "node_modules\\playwright-core"
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
