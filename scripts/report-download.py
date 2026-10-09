#!/usr/bin/env python3
import json
from pathlib import Path
import runpy

settings = runpy.run_path(str(Path(__file__).with_name('download-model.py')))
root = settings['ROOT']
reports = []
for name, size, sha in settings['FILES']:
    target = root / name
    marker = target.with_suffix('.gguf.verified.json')
    checkpoint = target.with_suffix('.gguf.ranges.json')
    verified = target.exists() and marker.exists()
    completed = size if verified else 0
    if not verified and checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        done = set(state['done'])
        chunk = 256 * 1024 * 1024
        completed = state['prefix'] + sum(min(start + chunk, size) - start
                    for start in range(state['prefix'], size, chunk) if start in done)
    reports.append({'file': name, 'size': size, 'completed': completed,
                    'verified': verified, 'verifying': completed == size and not verified})
pid_file = Path.home() / 'llama-rpc' / 'download.pid'
pid = int(pid_file.read_text()) if pid_file.exists() else None
command = Path('/proc') / str(pid) / 'cmdline'
running = command.exists() and b'download-model-parallel.py' in command.read_bytes()
print(json.dumps({'files': reports, 'completed': sum(item['completed'] for item in reports),
                  'total': sum(item['size'] for item in reports), 'running': running,
                  'ready': all(item['verified'] for item in reports)}), flush=True)
