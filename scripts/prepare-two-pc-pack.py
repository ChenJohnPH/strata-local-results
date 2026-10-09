import json
import os
from pathlib import Path
import subprocess
import sys

variant = sys.argv[1]
if variant not in ('IQ3_XXS', 'IQ3_S'):
    raise RuntimeError('Only the two retained full models are supported')
home = Path.home()
source = home/'Strata-two-pc-source/NTRYourWaifu-Strata-7add08d'
model = home/'llama-rpc/models'/variant/f'Qwen3.8-Flash-Next-GSQ-RCO-{variant}-00001-of-00002.gguf'
marker = json.loads(model.with_suffix('.gguf.verified.json').read_text())
if model.stat().st_size != marker['size'] or model.stat().st_mtime_ns != marker['mtime_ns']:
    raise RuntimeError('Model changed after validation')
out = home/'Strata-two-pc-data/packs'/variant.lower()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, STRATA_GGUF_PY=str(source/'third_party/llama.cpp/gguf-py'))
python = home/'Strata-speed/.venv/bin/python'
subprocess.run([str(python), str(source/'tools/iq_pack.py'), '--gguf', str(model), '--out', str(out)],
               env=env, check=True)
print('PACK_READY ' + str(out), flush=True)
