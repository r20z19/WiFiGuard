#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INTERFACE="${1:-wlan1mon}"

echo "============================================"
echo "  WiFiGuard 完整攻击演示脚本"
echo "  接口: $INTERFACE"
echo "============================================"
echo ""
echo "此脚本将依次执行所有攻击模拟。"
echo "请确保 $INTERFACE 已处于 monitor 模式。"
echo "按 Ctrl+C 可随时停止。"
echo ""

ATTACKS=(
    "模拟Deauth攻击:$SCRIPT_DIR/simulate_deauth.sh $INTERFACE"
    "模拟Evil Twin攻击:$SCRIPT_DIR/simulate_evil_twin.sh $INTERFACE"
    "模拟Flood泛洪:$SCRIPT_DIR/simulate_flood.sh $INTERFACE"
    "模拟暴力破解:$SCRIPT_DIR/simulate_brute_force.sh $INTERFACE"
    "模拟非法接入:$SCRIPT_DIR/simulate_illegal.sh $INTERFACE"
)

for attack in "${ATTACKS[@]}"; do
    NAME="${attack%%:*}"
    CMD="${attack#*:}"
    echo ""
    echo "--- $NAME ---"
    bash "$CMD"
    sleep 5
done

echo ""
echo "============================================"
echo "  演示结束"
echo "============================================"
