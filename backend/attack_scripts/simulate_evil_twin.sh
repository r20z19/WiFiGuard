#!/bin/bash
INTERFACE="${1:-wlan1}"
SSID="$2"
CHANNEL="$3"

if [ -z "$SSID" ] || [ -z "$CHANNEL" ]; then
    echo "用法: sudo $0 <接口> <SSID> <信道>"
    echo ""
    echo "示例: sudo $0 wlan1 hhhhhhhheeee 11"
    echo ""
    echo "提示: 运行 ./scan.sh 查看周围网络获取 SSID 和信道"
    exit 1
fi

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
