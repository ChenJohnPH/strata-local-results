import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

root = Path.home() / 'Strata-speed'
cfgfile = root / 'strata-q2_0.json'
baseline = root / 'strata-q2_0.baseline.json'
name = sys.argv[1]
presets = {'mmap-auto': (False, None, None), 'resident-auto': (True, None, None),
           'resident-15': (True, 15, None), 'resident-7': (True, 7, None),
           'resident-15-spec0': (True, 15, 0)}
presets['resident-15-spec2'] = (True, 15, 2)
if name not in presets:
    raise RuntimeError('Unknown Strata trial')
if not baseline.exists():
    baseline.write_text(cfgfile.read_text())
cfg = json.loads(baseline.read_text())
resident, workers, spec = presets[name]
args = cfg['args']
if resident:
    args = ['--resident-experts' if x == '--mmap-experts' else x for x in args]
    if '--resident-experts' not in args:
        args.append('--resident-experts')
def setarg(flag, value):
    if flag in args:
        args[args.index(flag)+1] = str(value)
    else:
        args.extend([flag, str(value)])
if workers is not None:
    setarg('--pool-workers', workers)
if spec is not None:
    setarg('--spec', spec)
cfg['args'] = args
cfg['aliases'] = ['qwen3.8-flash-next-125b-q2_0']
cfg['open_browser'] = False
subprocess.run(['python3', str(Path.home()/'llama-rpc/manage-strata.py'), 'stop'], check=True)
cfgfile.write_text(json.dumps(cfg, indent=2))
subprocess.run(['python3', str(Path.home()/'llama-rpc/manage-strata.py'), 'start'], check=True)
for _ in range(240):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3) as r:
            health = json.load(r)
        if health.get('loaded') is True and health.get('status') == 'ok':
            print('READY Strata ' + name, flush=True)
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise RuntimeError('Strata failed to become ready')
