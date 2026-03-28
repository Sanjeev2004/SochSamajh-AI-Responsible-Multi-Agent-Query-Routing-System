param(
    [int]$JudgeSampleSize = 0,
    [switch]$DisableLlmJudge
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPython = Join-Path $repoRoot "backend\venv\Scripts\python.exe"
$judgeScript = Join-Path $repoRoot "backend\evaluation\judge.py"

if (-not (Test-Path $backendPython)) {
    throw "Backend virtualenv Python not found: $backendPython"
}

if (-not (Test-Path $judgeScript)) {
    throw "Judge script not found: $judgeScript"
}

$arguments = @($judgeScript)

if ($JudgeSampleSize -gt 0) {
    $arguments += @("--judge-sample-size", "$JudgeSampleSize")
}

if ($DisableLlmJudge) {
    $arguments += "--disable-llm-judge"
}

& $backendPython @arguments
