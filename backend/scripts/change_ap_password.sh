#!/bin/bash
# 修改 AP 密码并重启 hostapd 使其生效
# 用法: sudo ./change_ap_password.sh <新密码>
# 示例: sudo ./change_ap_password.sh 12345678      # 弱密码测试
#       sudo ./change_ap_password.sh Str0ng!Pass#2026  # 强密码

CONF="/etc/hostapd/wifiguard.conf"

if [ "$(id -u)" -ne 0 ]; then
    echo "错误: 需要 root 权限，请使用 sudo 运行"
    exit 1
fi

if [ -z "$1" ]; then
    echo "用法: $0 <新密码>"
    echo ""
    echo "当前密码: $(grep '^wpa_passphrase=' "$CONF" | cut -d= -f2)"
    echo ""
    echo "弱密码示例（用于测试弱密码检测）:"
    echo "  $0 12345678"
    echo "  $0 password"
    echo "  $0 00000000"
    echo "  $0 wifi1234"
    echo ""
    echo "强密码示例:"
    echo "  $0 WIFIGuard2026"
    echo "  $0 Str0ng!Pass#2026"
    exit 0
fi

NEW_PASS="$1"

# WPA 密码长度要求: 8-63 个字符
if [ ${#NEW_PASS} -lt 8 ] || [ ${#NEW_PASS} -gt 63 ]; then
    echo "错误: WPA 密码长度必须在 8-63 个字符之间（当前: ${#NEW_PASS}）"
    exit 1
fi

# 读取当前密码
OLD_PASS=$(grep '^wpa_passphrase=' "$CONF" | cut -d= -f2)
echo "当前密码: $OLD_PASS"
echo "新密码:   $NEW_PASS"

# 修改 hostapd 配置文件
sed -i "s/^wpa_passphrase=.*/wpa_passphrase=$NEW_PASS/" "$CONF"

# 验证修改
VERIFY=$(grep '^wpa_passphrase=' "$CONF" | cut -d= -f2)
if [ "$VERIFY" != "$NEW_PASS" ]; then
    echo "错误: 密码修改失败"
    exit 1
fi

# 同步更新 start.py 的部署配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_CFG="$PROJECT_DIR/.deploy_config.json"

if [ -f "$DEPLOY_CFG" ]; then
    # 已有配置文件，更新 AP_PASS 字段
    sed -i "s/\"AP_PASS\": *\"[^\"]*\"/\"AP_PASS\": \"$NEW_PASS\"/" "$DEPLOY_CFG"
else
    # 创建配置文件，只写密码字段，start.py 会用默认值填充其余
    echo "{\"AP_PASS\": \"$NEW_PASS\"}" > "$DEPLOY_CFG"
fi

echo "✓ AP 密码已修改为: $NEW_PASS"
echo ""
echo "请重启 WiFiGuard 使新密码生效:"
echo "  sudo python3 start.py"
