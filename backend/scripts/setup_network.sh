#!/bin/bash
# WIFIGuard network setup: configure AP interface, monitor mode, nftables, and IP forwarding
set -e

# ── 从部署配置读取参数（支持覆盖） ──────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_CFG="$PROJECT_DIR/.deploy_config.json"

if [ -f "$DEPLOY_CFG" ]; then
    AP_IF="${AP_IF:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('AP_IF','wlan0'))")}"
    MON_IF="${MON_IF:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('MON_IF','wlan1'))")}"
    AP_IP="${AP_IP:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('AP_IP','10.77.0.1'))")}"
    AP_CHANNEL="${AP_CHANNEL:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('AP_CHANNEL','6'))")}"
    MGMT_IF="${MGMT_IF:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('MGMT_IF','eth0'))")}"
    MGMT_IP="${MGMT_IP:-$(python3 -c "import json;print(json.load(open('$DEPLOY_CFG')).get('MGMT_IP','10.99.0.1'))")}"
else
    AP_IF="${AP_IF:-wlan0}"
    MON_IF="${MON_IF:-wlan1}"
    AP_IP="${AP_IP:-10.77.0.1}"
    AP_CHANNEL="${AP_CHANNEL:-6}"
    MGMT_IF="${MGMT_IF:-eth0}"
    MGMT_IP="${MGMT_IP:-10.99.0.1}"
fi

echo "[*] WIFIGuard network setup starting..."
echo "    AP=$AP_IF  MON=$MON_IF  MGMT=$MGMT_IF"

# 1. Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# 2. Tell NetworkManager to leave AP interface alone
if command -v nmcli >/dev/null 2>&1; then
    nmcli device set "$AP_IF" managed no 2>/dev/null || true
fi

# 3. Configure AP interface with static IP
ip link set "$AP_IF" down 2>/dev/null || true
ip addr flush dev "$AP_IF" 2>/dev/null || true
ip addr add "$AP_IP/24" dev "$AP_IF"
ip link set "$AP_IF" up

# 4. Configure management interface
ip addr flush dev "$MGMT_IF" 2>/dev/null || true
ip addr add "$MGMT_IP/24" dev "$MGMT_IF" 2>/dev/null || true
ip link set "$MGMT_IF" up 2>/dev/null || true

# 5. Configure monitor interface
ip link set "$MON_IF" down 2>/dev/null || true
iw dev "$MON_IF" set type monitor 2>/dev/null || true
ip link set "$MON_IF" up
iw dev "$MON_IF" set channel "$AP_CHANNEL"

# 6. Load nftables rules
if [ -f /etc/nftables.d/wifiguard.nft ]; then
    nft -f /etc/nftables.d/wifiguard.nft
    echo "[+] nftables rules loaded"
fi

echo "[+] WIFIGuard network setup complete"
echo "    AP: $AP_IF ($AP_IP/24) channel $AP_CHANNEL"
echo "    Monitor: $MON_IF (channel $AP_CHANNEL)"
echo "    Management: $MGMT_IF ($MGMT_IP/24)"
