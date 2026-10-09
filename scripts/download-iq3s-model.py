#!/usr/bin/env python3
"""Resumable download of the pinned full Qwen model, with SHA256 validation."""
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request

ROOT = Path.home() / 'llama-rpc' / 'models' / 'IQ3_S'
REVISION = 'ed59f92082b1e93c0e96d60a8b11aab089b52f09'
FILES = [
    ('Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf',
     54817524224, '4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3'),
    ('Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf',
     28800138432, '316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113'),
]

def log(message):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), message, flush=True)

def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()

def fetch(name, size, sha256):
    target = ROOT / name
    partial = target.with_suffix('.gguf.part')
    marker = target.with_suffix('.gguf.verified.json')
    if target.exists() and target.stat().st_size == size:
        if marker.exists():
            previous = json.loads(marker.read_text())
            if previous.get('sha256') == sha256 and previous.get('mtime_ns') == target.stat().st_mtime_ns:
                log(f'Already verified: {name}')
                return
        log(f'Checking existing file: {name}')
        if digest(target) != sha256:
            raise RuntimeError(f'Existing file checksum mismatch: {target}')
    else:
        url = f'https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/resolve/{REVISION}/IQ3_S/{name}?download=true'
        for attempt in range(1, 9):
            position = partial.stat().st_size if partial.exists() else 0
            if position == size:
                break
            if position > size:
                raise RuntimeError(f'Partial file larger than expected: {partial}')
            headers = {'User-Agent': 'Qwen-local-install/1.0'}
            if position:
                headers['Range'] = f'bytes={position}-'
            log(f'Downloading {name}: {position / size:.1%}, attempt {attempt}')
            try:
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=90) as response:
                    if position and response.status != 206:
                        raise RuntimeError('Server did not honor resume range; preserving partial file')
                    if position and not response.headers.get('Content-Range', '').startswith(f'bytes {position}-'):
                        raise RuntimeError('Unexpected resume range; preserving partial file')
                    last_report = time.monotonic()
                    with partial.open('ab' if position else 'wb') as output:
                        while True:
                            chunk = response.read(4 * 1024 * 1024)
                            if not chunk:
                                break
                            output.write(chunk)
                            position += len(chunk)
                            if position > size:
                                raise RuntimeError('Download exceeds expected file size')
                            now = time.monotonic()
                            if now - last_report > 30:
                                log(f'{name}: {position / size:.1%} ({position / 1e9:.2f}/{size / 1e9:.2f} GB)')
                                last_report = now
                        output.flush()
                        os.fsync(output.fileno())
                if position != size:
                    raise RuntimeError(f'Incomplete transfer: {position}/{size}')
                break
            except Exception as error:
                log(f'Transfer interrupted: {error}')
                if attempt == 8:
                    raise
                time.sleep(min(attempt * 3, 20))
        log(f'Validating SHA256: {name}')
        if digest(partial) != sha256:
            raise RuntimeError(f'SHA256 mismatch: {partial}; file preserved for diagnosis')
        partial.replace(target)
    marker.write_text(json.dumps({'sha256': sha256, 'size': size,
                                 'mtime_ns': target.stat().st_mtime_ns,
                                 'revision': REVISION}, indent=2))
    log(f'Verified: {name}')

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    for item in FILES:
        fetch(*item)
    log('MODEL_DOWNLOAD_COMPLETE')
