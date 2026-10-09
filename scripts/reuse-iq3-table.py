import json
from pathlib import Path

root = Path.home() / 'llama-rpc' / 'models'
src = root/'Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf'
dst = root/'IQ3_XXS/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf'
expected = '316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113'
verified = json.loads(src.with_suffix('.gguf.verified.json').read_text())
if (verified['sha256'] != expected or src.stat().st_size != 28800138432
        or src.stat().st_mtime_ns != verified['mtime_ns']):
    raise RuntimeError('Shared table source is not verified')
dst.parent.mkdir(exist_ok=True)
if not dst.exists():
    dst.hardlink_to(src)
if dst.stat().st_ino != src.stat().st_ino:
    raise RuntimeError('Existing destination is not the verified shared table')
dst.with_suffix('.gguf.verified.json').write_text(json.dumps(verified, indent=2))
print('Reused verified identical 28.8GB lookup table', flush=True)
