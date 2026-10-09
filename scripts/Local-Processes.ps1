function Save-ManagedProcess {
    param($Process, [string]$Role)
    for ($taskAttempt = 0; $taskAttempt -lt 20; $taskAttempt++) {
        $Process = Get-Process -Id $Process.Id -ErrorAction Stop
        if ($Process.Path) { break }
        Start-Sleep -Milliseconds 50
    }
    if (-not $Process.Path) { throw "Cannot record executable path for $Role." }
    @{
        Pid = $Process.Id
        StartedUtc = $Process.StartTime.ToUniversalTime().ToString('o')
        StartedUtcTicks = $Process.StartTime.ToUniversalTime().Ticks
        Executable = $Process.Path
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot "$Role-process.json") -Encoding UTF8
    $Process.Id | Set-Content -LiteralPath (Join-Path $PSScriptRoot "$Role.pid")
}

function Get-ManagedProcess {
    param([string]$Role)
    $taskRecordPath = Join-Path $PSScriptRoot "$Role-process.json"
    if (-not (Test-Path -LiteralPath $taskRecordPath)) { return $null }
    $taskRecord = Get-Content -LiteralPath $taskRecordPath -Raw | ConvertFrom-Json
    $taskProcess = Get-Process -Id $taskRecord.Pid -ErrorAction SilentlyContinue
    if (-not $taskProcess) { return $null }
    $taskExpectedTicks = if ($taskRecord.StartedUtcTicks) { [long]$taskRecord.StartedUtcTicks } else {
        ([datetime]$taskRecord.StartedUtc).ToUniversalTime().Ticks
    }
    if ($taskProcess.Path -ne $taskRecord.Executable -or
        $taskProcess.StartTime.ToUniversalTime().Ticks -ne $taskExpectedTicks) {
        throw "Saved $Role PID belongs to another process; refusing to use it."
    }
    return $taskProcess
}
