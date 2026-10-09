param([switch]$NoBrowser, [ValidateRange(30,1800)][int]$ReadyTimeoutSeconds = 900)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Local-Processes.ps1')
$taskKey = Join-Path $PSScriptRoot 'ssh\id_ed25519'
$taskSsh = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$taskTarget = 'REMOTE_USER@DESKTOP_LAN_IP'
$taskNativeArgs = @('-i',$taskKey,'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=10',
    '-o','HostKeyAlias=DESKTOP_HOST_KEY_ALIAS','-o','StrictHostKeyChecking=yes')
& $taskSsh @taskNativeArgs $taskTarget 'python3 ~/llama-rpc/manage-server.py stop'
if ($LASTEXITCODE -ne 0) { throw 'RPC model could not stop before starting Strata.' }
$taskWorker = Get-ManagedProcess worker
if ($taskWorker) { Stop-Process -Id $taskWorker.Id }
if (-not (Get-ManagedProcess tunnel)) {
    $taskTunnelArgs = @('-i',"`"$taskKey`"",'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=10',
        '-o','HostKeyAlias=DESKTOP_HOST_KEY_ALIAS','-o','StrictHostKeyChecking=yes','-N','-T',
        '-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=30','-o','ServerAliveCountMax=3',
        '-L','127.0.0.1:8080:127.0.0.1:8080',$taskTarget)
    $taskTunnel = Start-Process -FilePath $taskSsh -ArgumentList $taskTunnelArgs -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $PSScriptRoot 'tunnel.out.log') `
        -RedirectStandardError (Join-Path $PSScriptRoot 'tunnel.err.log')
    Save-ManagedProcess $taskTunnel tunnel
    Start-Sleep -Seconds 2
    if ($taskTunnel.HasExited) { throw 'SSH tunnel exited. See tunnel.err.log.' }
}
& $taskSsh @taskNativeArgs $taskTarget 'python3 ~/llama-rpc/manage-strata.py start'
if ($LASTEXITCODE -ne 0) { throw 'Strata could not start. See ~/Strata-speed/managed-server.log.' }
$taskDeadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
while ((Get-Date) -lt $taskDeadline) {
    try {
        $taskHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/health' -TimeoutSec 3
        if ($taskHealth.status -eq 'ok' -and $taskHealth.loaded) {
            Write-Host 'Ready: http://127.0.0.1:8080'
            Write-Host 'API key: open ssh\strata-api-key.txt and use it when the web page or client asks.'
            if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8080/' }
            exit 0
        }
    } catch { }
    Start-Sleep -Seconds 3
}
throw 'Strata is not ready yet. Check ~/Strata-speed/managed-server.log.'
