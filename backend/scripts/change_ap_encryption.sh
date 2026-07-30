#!/bin/bash
# 切换 AP 加密协议/模式，用于测试弱加密检测功能
# 用法: sudo ./change_ap_encryption.sh <模式>
#
# 可用模式:
#   open        - 开放网络（无加密）
#   wep         - WEP 加密
#   wpa1        - WPA1 + TKIP
#   wpa1_aes    - WPA1 + AES
#   wpa2_tkip   - WPA2 + TKIP（弱）
#   wpa2        - WPA2 + AES（无 PMF）
#   wpa2_pmf    - WPA2 + AES + PMF（推荐，最高可用安全级别）
#   wpa3_transition - WPA3过渡模式（⚠ 树莓派5驱动不支持SAE）
#   wpa3        - WPA3-SAE（⚠ 树莓派5驱动不支持SAE）

CONF="/etc/hostapd/wifiguard.conf"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ "$(id -u)" -ne 0 ]; then
    echo "错误: 需要 root 权限，请使用 sudo 运行"
    exit 1
fi

show_usage() {
    echo "用法: $0 <模式>"
    echo ""
    echo "可用模式（按安全性从低到高）:"
    echo "  open        开放网络，无加密          → 触发检测"
    echo "  wep         WEP 加密                 → 触发检测"
    echo "  wpa1        WPA1 + TKIP              → 触发检测"
    echo "  wpa1_aes    WPA1 + AES               → 触发检测"
    echo "  wpa2_tkip   WPA2 + TKIP              → 触发检测"
    echo "  wpa2        WPA2 + AES, 无PMF        → 触发检测"
    echo "  wpa2_pmf    WPA2 + AES + PMF         → ✓ 推荐（最高可用安全级别）"
    echo "  wpa3_transition  WPA3过渡模式          → ⚠ 树莓派5不支持SAE"
    echo "  wpa3        WPA3-SAE                 → ⚠ 树莓派5不支持SAE"
    echo ""
    # 读取当前配置摘要
    if [ -f "$CONF" ]; then
        echo "当前配置:"
        grep -E '^(wpa=|wpa_key_mgmt=|rsn_pairwise=|wpa_pairwise=|ieee80211w=|wep_key|auth_algs=)' "$CONF" | sed 's/^/  /'
    fi
}

if [ -z "$1" ]; then
    show_usage
    exit 0
fi

MODE="$1"

# 读取当前密码（切换模式时保留密码）
CURRENT_PASS=$(grep '^wpa_passphrase=' "$CONF" 2>/dev/null | cut -d= -f2)
CURRENT_PASS="${CURRENT_PASS:-WIFIGuard2026}"

# 保留公共配置（非加密相关的部分）
generate_base() {
    cat <<EOF
# WiFiGuard AP Configuration
# 加密模式: $MODE (由 change_ap_encryption.sh 生成)
interface=wlan0
driver=nl80211
ssid=WIFIGuard-Lab
country_code=CN

# 2.4GHz, channel 6
hw_mode=g
channel=6
ieee80211n=1

# Performance
wmm_enabled=1

# Control interface for hostapd_cli
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0

# Logging
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2

EOF
}

case "$MODE" in
    open)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# 开放网络 - 无加密
auth_algs=1
wpa=0
EOF
        DESC="开放网络（无加密）"
        ;;

    wep)
        generate_base > "$CONF"
        # WEP 密码需要是 5 或 13 字符（ASCII），或 10/26 位十六进制
        WEP_KEY="1234567890"  # 10位十六进制
        cat >> "$CONF" <<EOF
# WEP 加密
auth_algs=1
wpa=0
wep_default_key=0
wep_key0=$WEP_KEY
EOF
        DESC="WEP 加密 (key: $WEP_KEY)"
        ;;

    wpa1)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA1 + TKIP
auth_algs=1
wpa=1
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
wpa_passphrase=$CURRENT_PASS
EOF
        DESC="WPA1 + TKIP"
        ;;

    wpa1_aes)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA1 + AES
auth_algs=1
wpa=1
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
wpa_passphrase=$CURRENT_PASS
EOF
        DESC="WPA1 + AES"
        ;;

    wpa2_tkip)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA2 + TKIP（弱加密算法）
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=TKIP
wpa_passphrase=$CURRENT_PASS
ieee80211w=0
EOF
        DESC="WPA2 + TKIP（弱算法）"
        ;;

    wpa2)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA2 + AES, 无 PMF
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=$CURRENT_PASS
ieee80211w=0
EOF
        DESC="WPA2 + AES（无 PMF）"
        ;;

    wpa2_pmf)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA2 + AES + PMF（安全配置）
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=$CURRENT_PASS
ieee80211w=2
EOF
        DESC="WPA2 + AES + PMF（安全）"
        ;;

    wpa3_transition)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA3 过渡模式: WPA2-PSK + WPA3-SAE 同时支持
# 新设备用 SAE，旧设备回退到 WPA2-PSK
auth_algs=1
wpa=2
wpa_key_mgmt=SAE WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=$CURRENT_PASS
ieee80211w=1
sae_require_mfp=1
EOF
        DESC="WPA3 过渡模式（WPA2+WPA3兼容）"
        ;;

    wpa3)
        generate_base > "$CONF"
        cat >> "$CONF" <<EOF
# WPA3-SAE（最安全）
auth_algs=1
wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
wpa_passphrase=$CURRENT_PASS
ieee80211w=2
sae_require_mfp=1
EOF
        DESC="WPA3-SAE（最安全）"
        ;;

    *)
        echo "错误: 未知模式 '$MODE'"
        echo ""
        show_usage
        exit 1
        ;;
esac

echo "✓ AP 加密已切换为: $DESC"
echo ""
echo "请重启 WiFiGuard 使配置生效:"
echo "  sudo python3 start.py"
