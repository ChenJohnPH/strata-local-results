"""Prime CUDA graphs and expert caches through the authenticated, local API."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.request

p = argparse.ArgumentParser()
p.add_argument('--url', default='http://127.0.0.1:8080')
p.add_argument('--model', required=True)
p.add_argument('--key-file', required=True)
p.add_argument('--tokens', type=int, default=64)
a = p.parse_args()
key = Path(a.key_file).read_text(encoding='utf-8-sig').strip()
prompts = [
    '請用繁體中文寫一篇至少一千字的科普文章，解釋颱風如何形成，直接開始正文。',
    'Write a complete Python implementation of an LRU cache with TTL expiration, thread safety, and example usage. Explain the design after the code.',
]
out = {'model': a.model, 'url': a.url, 'started_utc': datetime.now(timezone.utc).isoformat(), 'runs': []}
for index, prompt in enumerate(prompts):
    payload = {'model': a.model, 'messages': [{'role': 'user', 'content': prompt}],
               'max_tokens': a.tokens, 'temperature': 0, 'reasoning_effort': 'none',
               'chat_template_kwargs': {'enable_thinking': False}, 'stream': False}
    request = urllib.request.Request(a.url+'/v1/chat/completions', data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+key})
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
    content = data['choices'][0]['message'].get('content') or ''
    if not content.strip() or set(content.strip()) == {'0'}:
        raise RuntimeError('Warm-up returned invalid output')
    item = {'kind': ('prose', 'code')[index], 'elapsed_seconds': round(time.monotonic()-start, 3),
            'timings': data.get('timings'), 'usage': data.get('usage')}
    out['runs'].append(item)
    out['status'] = 'warming'
    Path(__file__).with_name('warmup-last.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('WARMUP '+json.dumps(item), flush=True)
out['status'] = 'ready'
out['finished_utc'] = datetime.now(timezone.utc).isoformat()
Path(__file__).with_name('warmup-last.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('WARMUP_READY '+a.model, flush=True)
