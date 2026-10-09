param(
    [ValidateRange(1024,65535)][int]$Port = 50052,
    [ValidateRange(1,64)][int]$Threads = 8
)
$ErrorActionPreference = 'Stop'
$env:LLAMA_CACHE = Join-Path $PSScriptRoot 'cache'
New-Item -ItemType Directory -Path $env:LLAMA_CACHE -Force | Out-Null
$taskExecutable = Join-Path $PSScriptRoot 'bin\ggml-rpc-server.exe'
if (-not (Test-Path -LiteralPath $taskExecutable)) { throw 'RPC executable is missing.' }
# Both devices are explicit: remote CPU layers can use laptop RAM.
# Keep this process running while the desktop is using its devices.
& $taskExecutable -H 127.0.0.1 -p $Port -d 'CUDA0,CPU' -t $Threads -c
exit $LASTEXITCODE
