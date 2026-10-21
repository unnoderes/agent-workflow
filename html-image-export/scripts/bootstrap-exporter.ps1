param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir,

    [switch]$InstallDeps,

    [switch]$ForceProjectSync
)

$ErrorActionPreference = "Stop"

$resolvedTarget = (Resolve-Path -LiteralPath $TargetDir).Path
$skillRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Join-Path $skillRoot "assets\\exporter-project"

$filesToSync = @(
    "package.json",
    "export-screenshots.js"
)

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

Write-Host "Exporting HTML files in $resolvedTarget"
npm run export:screenshots | Out-Host
