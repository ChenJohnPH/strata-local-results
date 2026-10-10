import argparse
import json
from pathlib import Path
import statistics
import time
import urllib.request

p = argparse.ArgumentParser()
p.add_argument('name')
p.add_argument('--runs', type=int, default=3)
p.add_argument('--tokens', type=int, default=96)
p.add_argument('--kind', choices=['digits', 'prose', 'code'], default='digits')
p.add_argument('--url', default='http://127.0.0.1:8080')
p.add_argument('--key-file')
p.add_argument('--model', default='qwen3.8-flash-next-iq3_xxs')
p.add_argument('--spec-min-p', type=float)
a = p.parse_args()
prompts = {
 'digits': '請依序輸出數字1到100，用逗號分隔，直接輸出數字。',
 'prose': '請用繁體中文寫一篇至少一千字的科普文章，解釋颱風如何形成，直接開始正文。',
 'code': 'Write a complete Python implementation of an LRU cache with TTL expiration, thread safety, and example usage. Explain the design after the code.',
}
results = []
for i in range(a.runs):
    payload = {'model': a.model,
      'messages': [{'role': 'user', 'content': prompts[a.kind]}],
      'max_tokens': a.tokens, 'temperature': 0, 'reasoning_effort': 'none',
      'chat_template_kwargs': {'enable_thinking': False}, 'stream': False}
    if a.spec_min_p is not None:
        payload['strata_tune'] = {'spec_min_p': a.spec_min_p}
    headers = {'Content-Type': 'application/json'}
    if a.key_file:
        headers['Authorization'] = 'Bearer ' + Path(a.key_file).read_text().strip()
    req = urllib.request.Request(a.url + '/v1/chat/completions',
      data=json.dumps(payload, ensure_ascii=False).encode(), headers=headers)
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=300) as response:
        data = json.load(response)
    item = {'elapsed': time.monotonic()-start, 'timings': data.get('timings'),
            'usage': data.get('usage'), 'content': data['choices'][0]['message'].get('content', '')}
    if not item['content'].strip() or set(item['content'].strip()) == {'0'}:
        raise RuntimeError('Invalid output')
    results.append(item)
    out = {'name': a.name, 'kind': a.kind, 'requested_tokens': a.tokens, 'runs': results}
    Path(__file__).with_name('bench-' + a.name + '-' + a.kind + '.json').write_text(
       json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'run': i+1, 'elapsed': round(item['elapsed'],2),
                     'timings': item['timings'], 'usage': item['usage']}), flush=True)
rates = [r['timings']['predicted_per_second'] for r in results
         if r['timings'] and 'predicted_per_second' in r['timings']]
if rates:
    print('median_decode_tok_s=' + str(statistics.median(rates)), flush=True)
