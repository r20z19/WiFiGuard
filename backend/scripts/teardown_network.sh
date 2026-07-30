#!/bin/bash
# WIFIGuard network teardown: restore interfaces to default state

# ── 从部署配置读取参数 ──────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_CFG="$PROJECT_DIR/.deploy_config.json"

if [ -f "$DEPLOY_CFG" ]; then
    AP_IF="${AP_IF:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('AP_IF','wlan0'))")}"
    MON_IF="${MON_IF:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('MON_IF','wlan1'))")}"
else
    AP_IF="${AP_IF:-wlan0}"
    MON_IF="${MON_IF:-wlan1}"
fi

echo "[*] WIFIGuard network teardown..."
echo "    AP=$AP_IF  MON=$MON_IF"

# Flush nftables
nft flush ruleset 2>/dev/null || true

# Restore monitor to managed
ip link set "$MON_IF" down 2>/dev/null || true
iw dev "$MON_IF" set type managed 2>/dev/null || true
ip link set "$MON_IF" up 2>/dev/null || true

# Restore AP interface
ip addr flush dev "$AP_IF" 2>/dev/null || true
ip link set "$AP_IF" down 2>/dev/null || true
iw dev "$AP_IF" set type managed 2>/dev/null || true
ip link set "$AP_IF" up 2>/dev/null || true

# Re-enable NetworkManager for AP interface
if command -v nmcli >/dev/null 2>&1; then
    nmcli device set "$AP_IF" managed yes 2>/dev/null || true
fi

echo "[+] Network teardown complete"
