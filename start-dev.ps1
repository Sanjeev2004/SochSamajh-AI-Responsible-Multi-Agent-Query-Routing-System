param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"

$backendPython = Join-Path $backendDir "venv\Scripts\python.exe"
$frontendNode = "node"
$frontendEntry = ".\node_modules\vite\bin\vite.js"

$backendLog = Join-Path $backendDir "backend-dev.log"
$backendErrLog = Join-Path $backendDir "backend-dev.err.log"
$frontendLog = Join-Path $frontendDir "frontend-dev.log"
$frontendErrLog = Join-Path $frontendDir "frontend-dev.err.log"
$pidFile = Join-Path $repoRoot ".dev-pids.json"

function Test-LocalUrl {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Attempts = 20,
        [int]$DelaySeconds = 1
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    return $false
}

function Ensure-Exists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

Ensure-Exists -Path $backendPython -Label "Backend virtualenv Python"
Ensure-Exists -Path (Join-Path $frontendDir $frontendEntry.TrimStart(".\")) -Label "Frontend Vite entry"

Write-Host ""
Write-Host "Starting backend..." -ForegroundColor Cyan
$backendProcess = Start-Process `
    -FilePath $backendPython `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$BackendPort" `
    -WorkingDirectory $backendDir `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError $backendErrLog `
    -PassThru

Write-Host "Starting frontend..." -ForegroundColor Cyan
$frontendProcess = Start-Process `
    -FilePath $frontendNode `
    -ArgumentList $frontendEntry, "--host", "127.0.0.1", "--port", "$FrontendPort" `
    -WorkingDirectory $frontendDir `
    -RedirectStandardOutput $frontendLog `
    -RedirectStandardError $frontendErrLog `
    -PassThru

$backendReady = Test-LocalUrl -Url "http://127.0.0.1:$BackendPort/api/health"
$frontendReady = Test-LocalUrl -Url "http://127.0.0.1:$FrontendPort"

Write-Host ""
Write-Host "Processes launched:" -ForegroundColor Green
Write-Host "Backend PID : $($backendProcess.Id)"
Write-Host "Frontend PID: $($frontendProcess.Id)"
Write-Host ""

$pidPayload = @{
    backend_pid = $backendProcess.Id
    frontend_pid = $frontendProcess.Id
    backend_port = $BackendPort
    frontend_port = $FrontendPort
} | ConvertTo-Json

Set-Content -Path $pidFile -Value $pidPayload

if ($backendReady) {
    Write-Host "Backend URL : http://127.0.0.1:$BackendPort" -ForegroundColor Green
} else {
    Write-Host "Backend did not respond in time. Check $backendErrLog" -ForegroundColor Yellow
}

if ($frontendReady) {
    Write-Host "Frontend URL: http://127.0.0.1:$FrontendPort" -ForegroundColor Green
} else {
    Write-Host "Frontend did not respond in time. Check $frontendErrLog" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "Backend : $backendLog"
Write-Host "Frontend: $frontendLog"
Write-Host "PID file : $pidFile"
Write-Host ""
Write-Host "To stop them later, run Stop-Process -Id $($backendProcess.Id),$($frontendProcess.Id)" -ForegroundColor DarkGray
