param(
    [string]$InstallPath = "$env:USERPROFILE\.arc-cli",
    [switch]$SystemWide
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $PSScriptRoot "arc.py"

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ARC CLI Installer                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verify Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Error: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $($python.Source)" -ForegroundColor Green

# Create install directory if needed
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}
Write-Host "✓ Install directory: $InstallPath" -ForegroundColor Green

# Create arc.bat entry point
$batContent = @"
@echo off
python "%~dp0arc.py" %*
"@
Set-Content -Path (Join-Path $InstallPath "arc.bat") -Value $batContent -Encoding ASCII

# Copy arc.py (with backend imports)
Copy-Item -Path $ScriptPath -Destination (Join-Path $InstallPath "arc.py") -Force
Write-Host "✓ Scripts copied" -ForegroundColor Green

# Add to PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$InstallPath*") {
    $newPath = "$userPath;$InstallPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✓ Added to PATH (User)" -ForegroundColor Green
} else {
    Write-Host "✓ Already in PATH" -ForegroundColor Green
}

# Install Python dependencies
$backendDir = Join-Path $ProjectRoot "backend"
if (Test-Path $backendDir) {
    Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
    pip install -e "$backendDir" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠  pip install had warnings (non-fatal)" -ForegroundColor Yellow
    }
}

Write-Host "`n╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Installation complete!              ║" -ForegroundColor Cyan
Write-Host "║                                      ║" -ForegroundColor Cyan
Write-Host "║  Usage:                              ║" -ForegroundColor Cyan
Write-Host "║    arc --repl        (interactive)   ║" -ForegroundColor Cyan
Write-Host "║    arc <task>        (single task)   ║" -ForegroundColor Cyan
Write-Host "║    arc --plan <task> (plan only)     ║" -ForegroundColor Cyan
Write-Host "║    arc --serve       (MCP server)    ║" -ForegroundColor Cyan
Write-Host "║                                      ║" -ForegroundColor Cyan
Write-Host "║  Set OPENCODE_API_KEY in .env first! ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
