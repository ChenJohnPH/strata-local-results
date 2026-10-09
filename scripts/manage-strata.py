import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path.home() / 'Strata-speed'
pidfile = root / 'managed-server.pid'
server = root / 'serve' / 'server.py'
def alive():
    if not pidfile.exists():
        return None
    pid = int(pidfile.read_text())
    try:
        args = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:
        return None
    if not any(args):
        return None
    if str(server).encode() not in args:
        raise RuntimeError('Strata PID identity does not match')
    return pid

action = sys.argv[1]
pid = alive()
if action == 'start':
    if not pid:
        cfg = root / 'strata-q2_0.json'
        if not cfg.exists():
            raise RuntimeError('Strata setup is not finished')
        env = dict(os.environ)
        env['STRATA_API_KEY'] = (root / 'api-key.txt').read_text().strip()
        with (root / 'managed-server.log').open('ab', buffering=0) as log:
            proc = subprocess.Popen([str(root / '.venv/bin/python'), str(server),
                '--engine', 'strata', '--config', str(cfg), '--host', '127.0.0.1', '--port', '8080'],
                cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True)
        pid = proc.pid
        pidfile.write_text(str(pid))
    print('Strata PID', pid, flush=True)
elif action == 'stop':
    if pid:
        if os.getpgid(pid) != pid:
            raise RuntimeError('Strata process group identity did not match')
        os.killpg(pid, signal.SIGTERM)
        for _ in range(100):
            if not alive():
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Strata did not stop')
    print('Strata stopped', flush=True)
else:
    print('Strata PID', pid, flush=True)
