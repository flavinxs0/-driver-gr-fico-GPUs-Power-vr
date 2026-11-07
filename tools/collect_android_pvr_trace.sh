#!/usr/bin/env bash
# Capture targeted Android graphics diagnostics after reproducing a Vulkan-driver failure.
# Usage: tools/collect_android_pvr_trace.sh [output-dir] [package-name]
set -euo pipefail
OUT="${1:-pvr-trace-$(date +%Y%m%d-%H%M%S)}"
PKG="${2:-io.github.belmantegu.dmc4recomp}"
ADB="${ADB:-adb}"
mkdir -p "$OUT"
command -v "$ADB" >/dev/null 2>&1 || { echo "adb not found; install Android platform-tools or set ADB=/path/to/adb" >&2; exit 1; }
"$ADB" get-state >/dev/null

capture() {
  local name="$1"; shift
  echo "[+] $name"
  "$ADB" "$@" >"$OUT/$name.txt" 2>&1 || echo "[capture failed: command returned $?]" >>"$OUT/$name.txt"
}

capture device-properties shell getprop
capture package-info shell dumpsys package "$PKG"
capture graphics-nodes shell sh -c 'ls -lZ /dev/dri /dev/pvrsrvkm /dev/ion /dev/dma_heap 2>&1'
capture kernel-modules shell sh -c 'cat /proc/modules 2>/dev/null | grep -Ei "pvr|rogue|drm|gpu|ged|ion" || true'
capture selinux-status shell getenforce
capture kernel-log shell sh -c 'dmesg 2>&1 | grep -Ei "pvr|rogue|drm|gpu|iommu|avc: denied|firmware|fault|error" | tail -n 1200'

# Keep the full logcat because loader failures may precede the app's final fallback message.
# Review and redact unrelated/private data before sharing the resulting file.
capture logcat logcat -d -v threadtime

cat >"$OUT/README.txt" <<EOF
Capture completed: $(date -Is)
Package: $PKG
No logs were cleared. Reproduce the issue immediately before running this script.
The logcat may contain unrelated personal/app data; review and redact before sharing.
Files: device-properties, package-info, graphics-nodes, kernel-modules,
selinux-status, kernel-log, logcat.
EOF

echo "[+] Diagnostics saved to $OUT"
