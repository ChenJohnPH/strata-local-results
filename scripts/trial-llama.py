"""Apply a named, reversible performance trial on the desktop."""
import sys
from pathlib import Path
import subprocess
import time
import urllib.request
import json

root = Path.home() / 'llama-rpc'
presets = {
    'gpu-dense-cpu30': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 30',
    'gpu-dense-cpu27': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 27',
    'gpu-dense-cpu27-cache': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 27 --moe-cache-mib 768',
    'gpu-dense-cpu27-cache1536': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 27 --moe-cache-mib 1536',
    'gpu-dense-cpu30-cache3072': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 30 --moe-cache-mib 3072',
    'gpu-dense-cpu33-cache5120': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 33 --moe-cache-mib 5120',
    'gpu-dense-cpu33-cache4096': '--gpu-layers 99 --tensor-split 42,7 --n-cpu-moe 33 --moe-cache-mib 4096',
}
name = sys.argv[1]
if name not in presets:
    raise RuntimeError('Unknown trial')
script = (root / 'run-desktop-head-local-16.sh').read_text()
script = script.replace('--gpu-layers 24 --tensor-split 12,5', presets[name])
subprocess.run(['python3', str(root / 'manage-server.py'), 'stop'], check=True)
(root / 'run-desktop.sh').write_text(script)
subprocess.run(['python3', str(root / 'manage-server.py'), 'start'], check=True)
for i in range(180):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3) as r:
            result = json.load(r)
        if result.get('status') == 'ok':
            print('READY ' + name, flush=True)
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise RuntimeError('Trial did not become ready')
