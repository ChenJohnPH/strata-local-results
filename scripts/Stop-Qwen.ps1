$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Local-Processes.ps1')
$taskKey = Join-Path $PSScriptRoot 'ssh\id_ed25519'
$taskSsh = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$taskRemoteStopped = $false
try {
    & $taskSsh -i $taskKey -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=8 `
        -o HostKeyAlias=DESKTOP_HOST_KEY_ALIAS -o StrictHostKeyChecking=yes `
        REMOTE_USER@DESKTOP_LAN_IP 'python3 ~/llama-rpc/manage-strata.py stop && python3 ~/llama-rpc/manage-server.py stop'
    $taskRemoteStopped = $LASTEXITCODE -eq 0
    if ($taskRemoteStopped) { Start-Sleep -Seconds 2 }
} finally {
    foreach ($taskRole in @('tunnel','worker')) {
        $taskProcess = Get-ManagedProcess $taskRole
        if ($taskProcess) {
            Stop-Process -Id $taskProcess.Id
            Write-Host "Stopped laptop $taskRole."
        }
    }
}
if (-not $taskRemoteStopped) {
    Write-Warning 'Desktop could not be reached. Its model process may still be running.'
    exit 1
}
Write-Host 'Stopped Qwen on both computers.'
