$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $repoRoot ".dev-pids.json"

if (-not (Test-Path $pidFile)) {
    Write-Host "No PID file found. Nothing to stop." -ForegroundColor Yellow
    exit 0
}

$pidData = Get-Content $pidFile -Raw | ConvertFrom-Json
$stoppedAny = $false

foreach ($entry in @(
    @{ Name = "Backend"; Id = $pidData.backend_pid },
    @{ Name = "Frontend"; Id = $pidData.frontend_pid }
)) {
    if (-not $entry.Id) {
        continue
    }

    try {
        $process = Get-Process -Id $entry.Id -ErrorAction Stop
        Stop-Process -Id $entry.Id -Force
        Write-Host "$($entry.Name) stopped (PID $($entry.Id))" -ForegroundColor Green
        $stoppedAny = $true
    } catch {
        Write-Host "$($entry.Name) was not running (PID $($entry.Id))" -ForegroundColor Yellow
    }
}

Remove-Item $pidFile -Force

if (-not $stoppedAny) {
    Write-Host "No running dev processes were found." -ForegroundColor Yellow
}
