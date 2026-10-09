import json
from pathlib import Path
import time
import urllib.request

payload = {'model':'qwen3.8-flash-next-125b-q2_0',
           'messages':[{'role':'user','content':'請依序輸出數字1到100，用逗號分隔，直接輸出數字。'}],
           'max_tokens':96,'temperature':0,'reasoning_effort':'none',
           'chat_template_kwargs':{'enable_thinking':False},'stream':False}
started=time.monotonic()
req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',
                           data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),
                           headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=180) as response:
    data=json.load(response)
summary={'elapsed_seconds':round(time.monotonic()-started,2), 'timings':data.get('timings'),
         'usage':data.get('usage'), 'content':data['choices'][0]['message'].get('content','')}
Path(__file__).with_name('profile-request.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
