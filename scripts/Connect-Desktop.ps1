param(
    [Parameter(Mandatory=$true)][string]$DesktopAddress,
    [Parameter(Mandatory=$true)][string]$UserName,
    [string]$IdentityFile = (Join-Path $PSScriptRoot 'ssh\id_ed25519'),
    [ValidateRange(1,65535)][int]$SshPort = 22,
    [ValidateRange(1024,65535)][int]$RpcPort = 50052,
    [ValidateRange(1024,65535)][int]$WebPort = 8080
)
$ErrorActionPreference = 'Stop'
if ($DesktopAddress -match '[\s@]' -or $DesktopAddress.StartsWith('-')) { throw 'Use a desktop IP address or hostname.' }
if ($UserName -match '[\s@]' -or $UserName.StartsWith('-')) { throw 'Use the desktop login username.' }
# Desktop -> laptop RPC, and laptop browser -> desktop model API.
# SSH performs the normal host-key and login checks; no passwords are stored.
& ssh.exe -N -T -p $SshPort `
    -i $IdentityFile `
    -o IdentitiesOnly=yes `
    -o ExitOnForwardFailure=yes `
    -o ServerAliveInterval=30 `
    -o ServerAliveCountMax=3 `
    -R "127.0.0.1:${RpcPort}:127.0.0.1:${RpcPort}" `
    -L "127.0.0.1:${WebPort}:127.0.0.1:${WebPort}" `
    "${UserName}@${DesktopAddress}"
exit $LASTEXITCODE
