#!/usr/bin/env python3
"""Start/stop only the model process created by this installation."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path.home() / 'llama-rpc'
PID_FILE = ROOT / 'server.pid'
EXE = str(ROOT / 'build' / 'bin' / 'llama-server')

def alive():
    if not PID_FILE.exists():
        return None
    pid = int(PID_FILE.read_text())
    command = Path('/proc') / str(pid) / 'cmdline'
    if not command.exists():
        return None
    raw = command.read_bytes()
    if not raw:
        return None
    args = raw.split(b'\0')
    expected = str(ROOT / 'run-desktop.sh').encode()
    if EXE.encode() not in args and expected not in args:
        raise RuntimeError('Saved PID belongs to a different process; refusing to act on it')
    return pid

action = sys.argv[1] if len(sys.argv) > 1 else 'status'
pid = alive()
if action == 'start':
    models = ROOT / 'models' / 'Q2_0'
    for name in ('Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf',
                 'Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf'):
        model = models / name
        marker = model.with_suffix('.gguf.verified.json')
        if not model.exists() or not marker.exists():
            raise RuntimeError('Model download/validation is not complete')
        verified = json.loads(marker.read_text())
        if model.stat().st_size != verified['size'] or model.stat().st_mtime_ns != verified['mtime_ns']:
            raise RuntimeError('Model file changed after verification')
    if not pid:
        with (ROOT / 'server.log').open('ab', buffering=0) as log:
            process = subprocess.Popen(['bash', str(ROOT / 'run-desktop.sh')],
                                       cwd=ROOT, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        pid = process.pid
        PID_FILE.write_text(str(pid))
    print(f'Server PID {pid}', flush=True)
elif action in ('stop', 'force-stop'):
    if pid:
        os.kill(pid, signal.SIGTERM)
        print(f'Sent stop to server PID {pid}', flush=True)
        for _ in range(100):
            if not alive():
                break
            time.sleep(0.1)
        else:
            if action == 'force-stop' and alive() == pid:
                os.kill(pid, signal.SIGKILL)
                print(f'Forced stop of verified model PID {pid}', flush=True)
            else:
                raise RuntimeError('Server did not stop within 10 seconds; worker must remain running')
    else:
        print('Server is not running', flush=True)
elif action == 'status':
    print(f'Server PID {pid}' if pid else 'Server is not running', flush=True)
else:
    raise RuntimeError('Use start, stop, force-stop, or status')
