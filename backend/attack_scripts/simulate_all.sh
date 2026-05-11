#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INTERFACE="${1:-wlp61s0mon}"

echo "============================================"
echo "  WiFiGuard 完整攻击演示脚本"
echo "============================================"
echo ""

if ! iwconfig "$INTERFACE" 2>/dev/null | grep -q "Mode:Monitor"; then
    echo "错误: $INTERFACE 不存在或未处于 monitor 模式"
    echo ""
    echo "请先执行:"
    echo "  sudo airmon-ng check kill"
    echo "  sudo airmon-ng start <网卡名>"
    exit 1
fi

# 获取当前连接信息
MY_ESSID=$(iwconfig 2>/dev/null | grep -oP 'ESSID:"\K[^"]+')
MY_BSSID=$(iwconfig 2>/dev/null | grep -oP 'Access Point: \K[0-9A-Fa-f:]{17}')
IFACE_MANAGED=$(echo "$INTERFACE" | sed 's/mon$//')

echo "当前连接: ${MY_ESSID:-未知}  (${MY_BSSID:-未知})"
echo "监听接口: $INTERFACE"
echo ""

<<<<<<< HEAD
run_attack() {
    local name="$1"
    local script="$2"
    shift 2
    echo ""
    echo "--- $name ---"
    bash "$script" "$@"
    sleep 5
}

run_attack "模拟Deauth攻击"     "$SCRIPT_DIR/simulate_deauth.sh"      "$INTERFACE"
run_attack "模拟Evil Twin攻击"  "$SCRIPT_DIR/simulate_evil_twin.sh"   "${INTERFACE%mon}"
run_attack "模拟Flood泛洪"      "$SCRIPT_DIR/simulate_flood.sh"       "$INTERFACE"
run_attack "模拟暴力破解"       "$SCRIPT_DIR/simulate_brute_force.sh" "$INTERFACE"
run_attack "模拟非法接入"       "$SCRIPT_DIR/simulate_illegal.sh"     "${INTERFACE%mon}"
=======
if [ -z "$MY_BSSID" ]; then
    echo "未检测到当前 WiFi 连接。请手动指定目标："
    echo ""
    echo "先运行 ./scan.sh 扫描，然后："
    echo "  sudo $0 $INTERFACE <AP的MAC> <SSID> <信道>"
    exit 1
fi

# 获取信道
TMPFILE=$(mktemp /tmp/wifiguard-scan.XXXXXX)
sudo airodump-ng --output-format csv -w "$TMPFILE" "$INTERFACE" &>/dev/null &
P=$!
sleep 4
sudo kill $P 2>/dev/null
sleep 1
CH=$(grep "$MY_BSSID" "${TMPFILE}-01.csv" 2>/dev/null | head -1 | cut -d',' -f4 | xargs)
CH="${CH:-6}"
rm -f "$TMPFILE" "${TMPFILE}-01.csv"

echo "目标 AP : $MY_BSSID"
echo "目标 SSID: $MY_ESSID"
echo "信道    : $CH"
echo ""
echo "即将依次执行 5 种攻击。确认这是你自己的网络！"
echo "按 Ctrl+C 取消，按 Enter 继续..."
read -r

run_attack() {
    local name="$1"
    shift
    echo ""
    echo "============================================"
    echo "  $name"
    echo "============================================"
    bash "$@"
    sleep 3
}

run_attack "Deauth 去认证攻击"        "$SCRIPT_DIR/simulate_deauth.sh"      "$INTERFACE" "$MY_BSSID" "FF:FF:FF:FF:FF:FF" 30
run_attack "Evil Twin 钓鱼 AP"       "$SCRIPT_DIR/simulate_evil_twin.sh"   "$IFACE_MANAGED" "$MY_ESSID" "$CH"
run_attack "Flood 泛洪攻击"          "$SCRIPT_DIR/simulate_flood.sh"       "$INTERFACE" "$MY_BSSID"
run_attack "暴力破解"                "$SCRIPT_DIR/simulate_brute_force.sh" "$INTERFACE" "$MY_BSSID"
run_attack "非法接入 (MAC 欺骗)"     "$SCRIPT_DIR/simulate_illegal.sh"     "$IFACE_MANAGED" "DE:AD:BE:EF:00:01"
>>>>>>> backend

echo ""
echo "============================================"
echo "  演示结束"
echo "============================================"
