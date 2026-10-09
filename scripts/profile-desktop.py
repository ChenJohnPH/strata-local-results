import json
import os
from pathlib import Path
import subprocess
import time

root = Path.home() / 'llama-rpc'
pid = int((root / 'server.pid').read_text())
hz = os.sysconf('SC_CLK_TCK')
nic = Path('/sys/class/net/wlp8s0/statistics')

def state():
    fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
    cpu = (int(fields[11]) + int(fields[12])) / hz
    io = dict(line.split(':', 1) for line in Path(f'/proc/{pid}/io').read_text().splitlines())
    net = sum(int((nic / name).read_text()) for name in ('rx_bytes', 'tx_bytes'))
    return time.monotonic(), cpu, int(io['read_bytes']), net

samples = []
previous = state()
started = time.monotonic()
while time.monotonic() - started < 45:
    time.sleep(0.5)
    current = state()
    dt = current[0] - previous[0]
    values = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                                     '--format=csv,noheader,nounits'], text=True).strip().split(',')
    samples.append({'seconds': round(current[0]-started, 2),
                    'cpu_percent_one_core': round(100*(current[1]-previous[1])/dt, 1),
                    'disk_MBps': round((current[2]-previous[2])/dt/1e6, 3),
                    'network_Mbps': round(8*(current[3]-previous[3])/dt/1e6, 3),
                    'gpu_percent': int(values[0]), 'gpu_memory_MiB': int(values[1])})
    previous = current
summary = {'duration': round(time.monotonic()-started,2), 'samples': samples,
           'cpu_avg': round(sum(x['cpu_percent_one_core'] for x in samples)/len(samples),1),
           'cpu_peak': max(x['cpu_percent_one_core'] for x in samples),
           'gpu_avg': round(sum(x['gpu_percent'] for x in samples)/len(samples),1),
           'gpu_peak': max(x['gpu_percent'] for x in samples),
           'network_avg_Mbps': round(sum(x['network_Mbps'] for x in samples)/len(samples),2),
           'network_peak_Mbps': max(x['network_Mbps'] for x in samples),
           'disk_avg_MBps': round(sum(x['disk_MBps'] for x in samples)/len(samples),3),
           'disk_peak_MBps': max(x['disk_MBps'] for x in samples)}
(root/'profile-desktop.json').write_text(json.dumps(summary, indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='samples'}), flush=True)
