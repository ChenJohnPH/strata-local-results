#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
    echo 'Run this script with sudo after approving the network driver installation.'
    exit 1
fi
task_source=/home/REMOTE_USER/llama-rpc/network-driver/r8126-10.016.00
task_archive=/home/REMOTE_USER/llama-rpc/network-driver/r8126-10.016.00.tar.bz2
printf '%s  %s\n' 50c8d3d49592d2e8f372bd7ece8e7df9b50a71b055c077d42eacc42302914440 "$task_archive" | sha256sum --check
test -f "$task_source/src/r8126.ko"
test "$(modinfo -F name "$task_source/src/r8126.ko")" = r8126
test "$(modinfo -F vermagic "$task_source/src/r8126.ko" | cut -d ' ' -f1)" = "$(uname -r)"
command -v dkms >/dev/null
command -v gcc-12 >/dev/null
task_target=/usr/src/r8126-10.016.00
if [ -e "$task_target" ]; then
    echo 'Driver source destination already exists; refusing to overwrite.'
    exit 1
fi
install -d "$task_target"
cp -a "$task_source/." "$task_target/"
cat >"$task_target/dkms.conf" <<'CONF'
PACKAGE_NAME="r8126"
PACKAGE_VERSION="10.016.00"
BUILT_MODULE_NAME[0]="r8126"
BUILT_MODULE_LOCATION[0]="src"
DEST_MODULE_LOCATION[0]="/updates/dkms"
AUTOINSTALL="yes"
MAKE[0]="make -C /lib/modules/${kernelver}/build M=${dkms_tree}/${PACKAGE_NAME}/${PACKAGE_VERSION}/build/src CC=gcc-12 modules"
CLEAN="make -C src clean"
CONF
dkms add -m r8126 -v 10.016.00
dkms build -m r8126 -v 10.016.00 -k "$(uname -r)"
dkms install -m r8126 -v 10.016.00 -k "$(uname -r)"
modprobe r8126
echo 'Driver installed. Wired interface status:'
ip -br addr
