param([switch]$NoBrowser, [ValidateRange(30,1800)][int]$ReadyTimeoutSeconds = 900)
$ErrorActionPreference = 'Stop'
$taskSelection = Join-Path $PSScriptRoot 'selected-engine.json'
if ((Test-Path -LiteralPath $taskSelection) -and
    (Get-Content -LiteralPath $taskSelection -Raw | ConvertFrom-Json).status -eq 'preparing') {
    Write-Host 'IQ3_XXS and IQ3_S are being prepared. Q2 has been removed.'
    exit 1
}
if ((Test-Path -LiteralPath $taskSelection) -and
    (Get-Content -LiteralPath $taskSelection -Raw | ConvertFrom-Json).engine -eq 'strata') {
    & (Join-Path $PSScriptRoot 'Start-Strata.ps1') -NoBrowser:$NoBrowser -ReadyTimeoutSeconds $ReadyTimeoutSeconds
    exit $LASTEXITCODE
}
. (Join-Path $PSScriptRoot 'Local-Processes.ps1')
$taskKey = Join-Path $PSScriptRoot 'ssh\id_ed25519'
$taskSsh = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$taskTarget = 'REMOTE_USER@DESKTOP_LAN_IP'
$taskBaseArgs = @('-i', "`"$taskKey`"", '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'HostKeyAlias=DESKTOP_HOST_KEY_ALIAS', '-o', 'StrictHostKeyChecking=yes')

if (-not (Get-ManagedProcess 'worker')) {
    $env:LLAMA_CACHE = Join-Path $PSScriptRoot 'cache'
    New-Item -ItemType Directory -Path $env:LLAMA_CACHE -Force | Out-Null
    $taskWorker = Start-Process -FilePath (Join-Path $PSScriptRoot 'bin\ggml-rpc-server.exe') `
        -ArgumentList @('-H','127.0.0.1','-p','50052','-d','CUDA0,CPU','-t','8','-c') `
        -WorkingDirectory (Join-Path $PSScriptRoot 'bin') -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $PSScriptRoot 'worker.out.log') `
        -RedirectStandardError (Join-Path $PSScriptRoot 'worker.err.log')
    Save-ManagedProcess $taskWorker 'worker'
    Start-Sleep -Seconds 1
    if ($taskWorker.HasExited) { throw 'RPC worker exited. See worker.err.log.' }
}

if (-not (Get-ManagedProcess 'tunnel')) {
    $taskTunnelArgs = $taskBaseArgs + @('-N','-T','-o','ExitOnForwardFailure=yes',
        '-o','ServerAliveInterval=30','-o','ServerAliveCountMax=3',
        '-R','127.0.0.1:50052:127.0.0.1:50052',
        '-L','127.0.0.1:8080:127.0.0.1:8080',$taskTarget)
    $taskTunnel = Start-Process -FilePath $taskSsh -ArgumentList $taskTunnelArgs `
        -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $PSScriptRoot 'tunnel.out.log') `
        -RedirectStandardError (Join-Path $PSScriptRoot 'tunnel.err.log')
    Save-ManagedProcess $taskTunnel 'tunnel'
    Start-Sleep -Seconds 2
    if ($taskTunnel.HasExited) { throw 'SSH tunnel exited. See tunnel.err.log.' }
}

# Native invocation needs unquoted argument values, unlike Start-Process.
$taskNativeArgs = @('-i',$taskKey,'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostKeyAlias=DESKTOP_HOST_KEY_ALIAS','-o','StrictHostKeyChecking=yes')
& $taskSsh @taskNativeArgs $taskTarget 'python3 ~/llama-rpc/manage-server.py start'
if ($LASTEXITCODE -ne 0) { throw 'Desktop server could not start. The model download must be complete.' }

Write-Host 'Loading Qwen on the desktop and laptop. Keep both computers awake.'
$taskDeadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
while ((Get-Date) -lt $taskDeadline) {
    try {
        $taskHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/health' -TimeoutSec 3
        if ($taskHealth.status -eq 'ok') {
            Write-Host 'Ready: http://127.0.0.1:8080'
            if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8080' }
            exit 0
        }
    } catch { }
    Start-Sleep -Seconds 3
}
throw 'Model is not ready yet. Check ~/llama-rpc/server.log on the desktop.'
