#!/bin/bash
INTERFACE="${1:-wlan1}"
SPOOF_MAC="$2"

if [ -z "$SPOOF_MAC" ]; then
    echo "用法: sudo $0 <接口> <伪造MAC>"
    echo ""
    echo "示例: sudo $0 wlan1 DE:AD:BE:EF:00:01"
    echo ""
    echo "提示: 运行 ./scan.sh 查看合法客户端 MAC"
    exit 1
fi

echo "[WiFiGuard] 模拟非法接入（MAC欺骗）..."
echo "  接口: $INTERFACE"
echo "  伪造 MAC: $SPOOF_MAC"

ORIGINAL_MAC=$(cat /sys/class/net/"$INTERFACE"/address 2>/dev/null)
echo "  原始 MAC: $ORIGINAL_MAC"

sudo ip link set "$INTERFACE" down
if command -v macchanger &>/dev/null; then
    sudo macchanger -m "$SPOOF_MAC" "$INTERFACE"
else
    sudo ip link set dev "$INTERFACE" address "$SPOOF_MAC"
fi
sudo ip link set "$INTERFACE" up

echo "  MAC 已更改为 $SPOOF_MAC"
sleep 10

if [ -n "$ORIGINAL_MAC" ]; then
    echo "  恢复原始 MAC..."
    sudo ip link set "$INTERFACE" down
    if command -v macchanger &>/dev/null; then
        sudo macchanger -m "$ORIGINAL_MAC" "$INTERFACE"
    else
        sudo ip link set dev "$INTERFACE" address "$ORIGINAL_MAC"
    fi
    sudo ip link set "$INTERFACE" up
    echo "  MAC 已恢复"
fi
