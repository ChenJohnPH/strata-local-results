import argparse
import json
from pathlib import Path
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--long', action='store_true')
parser.add_argument('--long-tokens', type=int, default=2800)
parser.add_argument('--key-file')
args = parser.parse_args()
root = Path(__file__).parent

def request(path, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    headers = {'Content-Type': 'application/json'}
    if args.key_file:
        headers['Authorization'] = 'Bearer ' + Path(args.key_file).read_text(encoding='utf-8').strip()
    req = urllib.request.Request('http://127.0.0.1:8080' + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)

health = request('/health')
print('Health:', json.dumps(health, ensure_ascii=False), flush=True)
prompt = '請用繁體中文，一句話說明模型分層運算。'
if args.long:
    prompt = ('This is padding used to test a long prompt. ' * (args.long_tokens // 10)
              + '\nIgnore the padding. Reply exactly with: RPC_OK')
    count = len(request('/tokenize', {'content': prompt})['tokens'])
    if not 2500 < count < 15000:
        raise RuntimeError(f'Unexpected long prompt token count: {count}')
    print(f'Long prompt has {count} tokens', flush=True)

started = time.monotonic()
result = request('/v1/chat/completions', {
    'model': 'qwen3.8-flash-next-125b-q2_0',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 128 if args.long else 256,
    'temperature': 0.0,
    'reasoning_effort': 'none',
    'chat_template_kwargs': {'enable_thinking': False},
    'stream': False,
})
elapsed = time.monotonic() - started
content = result['choices'][0]['message'].get('content', '')
if not content.strip() or set(content.strip()) == {'0'}:
    raise RuntimeError(f'Invalid model response: {result}')
if args.long and 'RPC_OK' not in content:
    raise RuntimeError(f'Long prompt verification failed: {result}')
summary = {'test': 'long' if args.long else 'chinese', 'elapsed_seconds': round(elapsed, 2),
           'content': content, 'usage': result.get('usage'), 'timings': result.get('timings'),
           'finish_reason': result['choices'][0].get('finish_reason'), 'health': health}
(root / ('verification-long.json' if args.long else 'verification-chinese.json')).write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
