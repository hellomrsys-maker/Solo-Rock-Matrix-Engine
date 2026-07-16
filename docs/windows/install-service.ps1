# SOLO ROCK Windows Service Installer
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install-service.ps1

#Requires -RunAsAdministrator

param(
    [string]$ServiceName = "SoloRock",
    [string]$DisplayName = "SOLO ROCK Hardware Orchestrator",
    [string]$Description = "Real-time CPU/GPU thermal management and hardware orchestration",
    [string]$InstallPath = "C:\Program Files\Solo-Rock"
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  SOLO ROCK Windows Service Installer" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Verify running as Administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Exit 1
}

# Check if Python is installed
Write-Host "Checking for Python installation..." -ForegroundColor Yellow
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "ERROR: Python not found. Please install Python 3.10+ first." -ForegroundColor Red
    Exit 1
}
Write-Host "  ✓ Found Python: $pythonExe" -ForegroundColor Green

# Check Python version
$pythonVersion = & $pythonExe --version 2>&1
Write-Host "  ✓ Version: $pythonVersion" -ForegroundColor Green

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Stopping existing $ServiceName service..." -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "Removing existing $ServiceName service..." -ForegroundColor Yellow
    & sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

# Determine script path
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
$monitorScript = Join-Path $repoRoot "monitor_realtime.py"

if (-not (Test-Path $monitorScript)) {
    Write-Host "ERROR: monitor_realtime.py not found at $monitorScript" -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "Creating Windows service..." -ForegroundColor Yellow
Write-Host "  Service Name: $ServiceName" -ForegroundColor Cyan
Write-Host "  Display Name: $DisplayName" -ForegroundColor Cyan
Write-Host "  Binary Path: $pythonExe" -ForegroundColor Cyan
Write-Host "  Script: $monitorScript" -ForegroundColor Cyan
Write-Host ""

# Create service using sc.exe
$binaryPath = "`"$pythonExe`" `"$monitorScript`" --duration 0"

try {
    & sc.exe create $ServiceName `
        binPath= $binaryPath `
        DisplayName= $DisplayName `
        start= auto | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Service created successfully" -ForegroundColor Green
    } else {
        throw "sc.exe returned exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "  ✗ Failed to create service: $_" -ForegroundColor Red
    Exit 1
}

# Set service description
try {
    & sc.exe description $ServiceName $Description | Out-Null
    Write-Host "  ✓ Description set" -ForegroundColor Green
} catch {
    Write-Host "  ! Warning: Could not set description" -ForegroundColor Yellow
}

# Set service to run as SYSTEM (default for sc.exe)
Write-Host "  ✓ Service configured to run as SYSTEM account" -ForegroundColor Green

# Start the service
Write-Host ""
Write-Host "Starting $ServiceName service..." -ForegroundColor Yellow
try {
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 2
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-Host "  ✓ Service started successfully" -ForegroundColor Green
    } else {
        Write-Host "  ! Service created but not running. Check Event Viewer for errors." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ! Failed to start service immediately: $_" -ForegroundColor Yellow
    Write-Host "  The service may start on next reboot." -ForegroundColor Yellow
}

# Display next steps
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Installation Complete" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Create config file:"
Write-Host "     Create: C:\Program Files\Solo-Rock\config.yaml" -ForegroundColor Cyan
Write-Host "     (Copy and customize from docs/config/thresholds.yaml)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Set environment variables (for alerting credentials):" -ForegroundColor Yellow
Write-Host "     [Environment]::SetEnvironmentVariable('SOLO_ROCK_EMAIL_USER', 'your-email', 'Machine')" -ForegroundColor Cyan
Write-Host "     [Environment]::SetEnvironmentVariable('SOLO_ROCK_EMAIL_PASS', 'your-password', 'Machine')" -ForegroundColor Cyan
Write-Host "     [Environment]::SetEnvironmentVariable('SOLO_ROCK_SLACK_WEBHOOK', 'webhook-url', 'Machine')" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Manage the service:" -ForegroundColor Yellow
Write-Host "     Start:   Start-Service SoloRock" -ForegroundColor Cyan
Write-Host "     Stop:    Stop-Service SoloRock" -ForegroundColor Cyan
Write-Host "     Restart: Restart-Service SoloRock" -ForegroundColor Cyan
Write-Host "     Status:  Get-Service SoloRock" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. View logs:" -ForegroundColor Yellow
Write-Host "     Event Viewer → Windows Logs → Application → Source: $ServiceName" -ForegroundColor Cyan
Write-Host ""
Write-Host "  5. Uninstall:" -ForegroundColor Yellow
Write-Host "     Run: .\docs\windows\uninstall-service.ps1" -ForegroundColor Cyan
Write-Host ""
