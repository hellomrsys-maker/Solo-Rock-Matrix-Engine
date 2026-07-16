# SOLO ROCK Windows Service Uninstaller
# Run as Administrator: powershell -ExecutionPolicy Bypass -File uninstall-service.ps1

#Requires -RunAsAdministrator

param(
    [string]$ServiceName = "SoloRock"
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  SOLO ROCK Windows Service Uninstaller" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Verify running as Administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Exit 1
}

# Check if service exists
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "ERROR: Service '$ServiceName' not found" -ForegroundColor Red
    Exit 1
}

# Confirm uninstall
Write-Host "This will uninstall the $ServiceName service." -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Continue? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    Exit 0
}

Write-Host ""

# Stop service if running
if ($service.Status -eq "Running") {
    Write-Host "Stopping $ServiceName service..." -ForegroundColor Yellow
    try {
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Service stopped" -ForegroundColor Green
    } catch {
        Write-Host "  ! Failed to stop service: $_" -ForegroundColor Yellow
    }
}

# Remove service
Write-Host "Removing $ServiceName service..." -ForegroundColor Yellow
try {
    & sc.exe delete $ServiceName | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Service removed" -ForegroundColor Green
    } else {
        throw "sc.exe returned exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "  ✗ Failed to remove service: $_" -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Uninstallation Complete" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The $ServiceName service has been removed." -ForegroundColor Green
Write-Host ""
Write-Host "Optional cleanup:" -ForegroundColor Yellow
Write-Host "  Remove installation directory:"
Write-Host "    rmdir /s /q C:\Program Files\Solo-Rock" -ForegroundColor Cyan
Write-Host ""
