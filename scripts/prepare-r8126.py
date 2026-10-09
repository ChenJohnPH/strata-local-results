"""Download a checksum-pinned Realtek source archive from OpenWrt; compile only."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

root = Path.home() / 'llama-rpc' / 'network-driver'
root.mkdir(exist_ok=True)
url = 'https://github.com/openwrt/rtl8126/releases/download/10.016.00/r8126-10.016.00.tar.bz2'
expected = '50c8d3d49592d2e8f372bd7ece8e7df9b50a71b055c077d42eacc42302914440'
archive = root / 'r8126-10.016.00.tar.bz2'
if not archive.exists():
    urllib.request.urlretrieve(url, archive)
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != expected:
    raise RuntimeError('Source archive SHA256 did not match OpenWrt package manifest')
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        name = Path(member.name)
        if name.is_absolute() or '..' in name.parts or member.issym() or member.islnk():
            raise RuntimeError('Unexpected archive path')
    tar.extractall(root)
source = root / 'r8126-10.016.00' / 'src'
kernel = subprocess.check_output(['uname', '-r'], text=True).strip()
args = ['make', '-C', '/lib/modules/' + kernel + '/build', 'M=' + str(source), '-j4', 'modules']
if shutil.which('gcc-12'):
    args.append('CC=gcc-12')
subprocess.run(args, check=True)
subprocess.run(['modinfo', str(source / 'r8126.ko')], check=True)
(root / 'prepared.json').write_text(json.dumps({'source': url, 'sha256': actual, 'kernel': kernel,
    'module': str(source / 'r8126.ko'), 'installed': False}, indent=2))
print('Driver compiled, NOT installed', flush=True)
