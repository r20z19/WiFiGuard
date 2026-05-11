#!/bin/bash
INTERFACE="${1:-wlp61s0mon}"
DURATION="${2:-10}"

echo "正在扫描 WiFi 网络 (${DURATION}s)..."
echo ""

TMPFILE=$(mktemp /tmp/wifiguard-scan.XXXXXX)
sudo airodump-ng --output-format csv -w "$TMPFILE" "$INTERFACE" &>/dev/null &
AIRODUMP_PID=$!
sleep "$DURATION"
sudo kill $AIRODUMP_PID 2>/dev/null
sleep 1

CSV="${TMPFILE}-01.csv"

if [ ! -f "$CSV" ]; then
    echo "错误: 扫描失败，请确认 $INTERFACE 处于 monitor 模式"
    exit 1
fi

# 获取当前连接的 AP 信息
MY_ESSID=$(iwconfig 2>/dev/null | grep -oP 'ESSID:"\K[^"]+')
MY_BSSID=$(iwconfig 2>/dev/null | grep -oP 'Access Point: \K[0-9A-Fa-f:]{17}')

echo "============================================"
echo "  你的连接"
echo "============================================"
if [ -n "$MY_ESSID" ]; then
    echo "  SSID : $MY_ESSID"
    echo "  BSSID: $MY_BSSID"
else
    echo "  未检测到当前 WiFi 连接"
fi

echo ""
echo "============================================"
echo "  扫描到的 AP 列表"
echo "============================================"
printf "  %-18s %4s  %s\n" "BSSID" "信道" "SSID"
printf "  %-18s %4s  %s\n" "------------------" "----" "----"

declare -a AP_LIST
while IFS=',' read -r bssid first_seen last_seen channel speed privacy cipher auth power beacons iv ip id essid key; do
    bssid=$(echo "$bssid" | xargs)
    channel=$(echo "$channel" | xargs)
    essid=$(echo "$essid" | xargs)
    if [[ "$bssid" =~ ^[0-9A-Fa-f:]{17}$ ]] && [ -n "$essid" ]; then
        printf "  %-18s %4s  %s\n" "$bssid" "$channel" "$essid"
        AP_LIST+=("$bssid|$channel|$essid")
    fi
done < <(grep -v '^$' "$CSV" | grep -v 'BSSID' | grep -v 'Station MAC')

if [ ${#AP_LIST[@]} -eq 0 ]; then
    echo "  未发现任何 AP"
    rm -f "$TMPFILE" "$CSV"
    exit 1
fi

echo ""
echo "============================================"
echo "  推荐命令"
echo "============================================"
echo ""

FIRST_AP="${AP_LIST[0]}"
IFS='|' read -r BSSID CH SSID_NAME <<< "$FIRST_AP"

IFACE_MANAGED=$(echo "$INTERFACE" | sed 's/mon$//')

[ -n "$MY_BSSID" ] && TARGET_BSSID="$MY_BSSID" || TARGET_BSSID="$BSSID"
[ -n "$MY_ESSID" ] && TARGET_SSID="$MY_ESSID" || TARGET_SSID="$SSID_NAME"

cat << CMD
# Deauth 去认证攻击（针对当前连接的 AP）
sudo ./simulate_deauth.sh $INTERFACE $TARGET_BSSID FF:FF:FF:FF:FF:FF

# Evil Twin 钓鱼 AP
sudo ./simulate_evil_twin.sh $IFACE_MANAGED "$TARGET_SSID" $CH

# Flood 泛洪攻击
sudo ./simulate_flood.sh $INTERFACE $TARGET_BSSID

# 暴力破解
sudo ./simulate_brute_force.sh $INTERFACE $TARGET_BSSID

# MAC 欺骗非法接入
sudo ./simulate_illegal.sh $IFACE_MANAGED DE:AD:BE:EF:00:01

CMD

echo "# 一键完整演示"
echo "sudo ./simulate_all.sh $INTERFACE"
echo ""

rm -f "$TMPFILE" "$CSV"
