#!/bin/bash
INTERFACE="${1:-wlan1}"
SSID="${2:-WiFiGuard-Network}"
CHANNEL="${3:-6}"

echo "[WiFiGuard] 模拟Evil Twin钓鱼AP..."
echo "  接口: $INTERFACE"
echo "  SSID: $SSID"
echo "  信道: $CHANNEL"

cat > /tmp/hostapd-evil.conf << EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
macaddr_acl=0
ignore_broadcast_ssid=0
EOF

echo "  启动伪造AP... 按 Ctrl+C 停止"
sudo hostapd /tmp/hostapd-evil.conf
