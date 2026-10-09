#!/usr/bin/env python3
"""Download disjoint HTTP ranges; resume checkpoints and verify the final file."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import runpy
import threading
import time
import urllib.request

settings = runpy.run_path(str(Path(__file__).with_name('download-iq3-model.py')))
ROOT, FILES, REVISION = (settings[key] for key in ('ROOT', 'FILES', 'REVISION'))
log, digest = (settings[key] for key in ('log', 'digest'))
CHUNK = 256 * 1024 * 1024
WORKERS = 16

def download(name, size, expected):
    target = ROOT / name
    if target.exists():
        settings['fetch'](name, size, expected)
        return
    partial = target.with_suffix('.gguf.part')
    checkpoint = target.with_suffix('.gguf.ranges.json')
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state['size'] != size or state['sha256'] != expected:
            raise RuntimeError('Resume metadata does not match the pinned model')
        if not partial.exists() or partial.stat().st_size != size:
            raise RuntimeError('Checkpoint file and partial file disagree')
    else:
        prefix = partial.stat().st_size if partial.exists() else 0
        if prefix > size:
            raise RuntimeError('Partial file exceeds expected size')
        state = {'size': size, 'sha256': expected, 'prefix': prefix, 'done': []}
        with partial.open('ab') as stream:
            stream.truncate(size)
        checkpoint.write_text(json.dumps(state))
    ranges = [(start, min(start + CHUNK, size))
              for start in range(state['prefix'], size, CHUNK)]
    done = set(state['done'])
    pending = [(start, end) for start, end in ranges if start not in done]
    lock = threading.Lock()
    last_report = [0.0]
    log(f'{name}: {WORKERS} streams, {len(pending)} remaining ranges')

    def transfer(start, end):
        for attempt in range(1, 9):
            position = start
            url = (f'https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/'
                   f'resolve/{REVISION}/IQ3_XXS/{name}?download=true&range={start}')
            request = urllib.request.Request(url, headers={
                'Range': f'bytes={start}-{end - 1}', 'User-Agent': 'Qwen-local-install/1.0'})
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    if response.status != 206 or not response.headers.get('Content-Range', '').startswith(f'bytes {start}-{end-1}/'):
                        raise RuntimeError('Server did not honor exact requested range')
                    with partial.open('r+b', buffering=0) as stream:
                        stream.seek(start)
                        while position < end:
                            data = response.read(min(4 * 1024 * 1024, end - position))
                            if not data:
                                raise RuntimeError('Early EOF while downloading range')
                            stream.write(data)
                            position += len(data)
                        os.fsync(stream.fileno())
                with lock:
                    done.add(start)
                    state['done'] = sorted(done)
                    temp = checkpoint.with_suffix('.json.tmp')
                    temp.write_text(json.dumps(state))
                    temp.replace(checkpoint)
                    now = time.monotonic()
                    if now - last_report[0] > 30 or len(done) == len(ranges):
                        downloaded = state['prefix'] + sum(b - a for a, b in ranges if a in done)
                        log(f'{name}: {downloaded / size:.1%} ({downloaded/1e9:.2f}/{size/1e9:.2f} GB)')
                        last_report[0] = now
                return
            except Exception as error:
                log(f'Range {start}-{end-1}, attempt {attempt}: {error}')
                if attempt == 8:
                    raise
                time.sleep(min(3 * attempt, 20))

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(transfer, start, end) for start, end in pending]
        for future in as_completed(futures):
            future.result()
    log(f'Validating SHA256: {name}')
    if digest(partial) != expected:
        raise RuntimeError(f'SHA256 mismatch: {partial}; file preserved')
    partial.replace(target)
    marker = target.with_suffix('.gguf.verified.json')
    marker.write_text(json.dumps({'sha256': expected, 'size': size,
                                 'mtime_ns': target.stat().st_mtime_ns,
                                 'revision': REVISION}, indent=2))
    log(f'Verified: {name}')

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    for item in FILES:
        download(*item)
    log('MODEL_DOWNLOAD_COMPLETE')
