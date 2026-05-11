#!/bin/bash
INTERFACE="${1:-wlan1}"
SPOOF_MAC="${2:-66:77:88:99:AA:01}"

echo "[WiFiGuard] 模拟非法接入（MAC欺骗）..."
echo "  接口: $INTERFACE"
echo "  伪造MAC: $SPOOF_MAC"

ORIGINAL_MAC=$(cat /sys/class/net/"$INTERFACE"/address)
echo "  原始MAC: $ORIGINAL_MAC"

sudo ip link set "$INTERFACE" down
sudo macchanger -m "$SPOOF_MAC" "$INTERFACE"
sudo ip link set "$INTERFACE" up

echo "  MAC已更改为 $SPOOF_MAC，尝试连接网络..."

sleep 10

echo "  恢复原始MAC..."
sudo ip link set "$INTERFACE" down
sudo macchanger -m "$ORIGINAL_MAC" "$INTERFACE"
sudo ip link set "$INTERFACE" up
echo "  MAC已恢复: $ORIGINAL_MAC"
