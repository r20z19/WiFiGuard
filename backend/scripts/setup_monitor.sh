#!/bin/bash
# setup_monitor.sh - Put a wireless interface into monitor mode for WiFiGuard
#
# Usage: sudo ./setup_monitor.sh [interface] [channel]
# Default interface: first wireless interface reported by iw dev
#
# This script:
#   1. Takes the interface down
#   2. Switches it to monitor mode
#   3. Brings it back up
#   4. Optionally locks the monitor interface to a channel
#   5. Verifies monitor mode is active
#   6. Prints the env vars to set for WiFiGuard
#
# Alternative: use airmon-ng (renames interface to wlan1mon):
#   sudo airmon-ng check kill
#   sudo airmon-ng start wlp0s20f0u1

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "[!] Please run as root: sudo $0 [interface] [channel]"
    exit 1
fi

detect_iface() {
    iw dev 2>/dev/null | awk '/Interface/ {print $2; exit}'
}

IFACE="${1:-$(detect_iface)}"
CHANNEL="${2:-${WIFIGUARD_CHANNEL:-}}"

if [ -z "$IFACE" ]; then
    echo "[!] No wireless interface found. Attach the USB wireless adapter first."
    exit 1
fi

echo "[*] Setting up monitor mode on $IFACE..."

if ! iw dev "$IFACE" info &>/dev/null; then
    echo "[!] Interface $IFACE not found. Available interfaces:"
    iw dev 2>/dev/null | grep Interface | awk '{print "    " $2}'
    exit 1
fi

if iw dev "$IFACE" info 2>/dev/null | grep -q "type monitor"; then
    echo "[*] $IFACE is already in monitor mode"
else
    if command -v nmcli >/dev/null 2>&1; then
        echo "[*] Asking NetworkManager to leave $IFACE unmanaged..."
        nmcli device disconnect "$IFACE" >/dev/null 2>&1 || true
        nmcli device set "$IFACE" managed no >/dev/null 2>&1 || true
    fi

    echo "[*] Bringing $IFACE down..."
    ip link set "$IFACE" down

    echo "[*] Setting type to monitor..."
    iw dev "$IFACE" set type monitor

    echo "[*] Bringing $IFACE up..."
    ip link set "$IFACE" up
fi

if [ -n "$CHANNEL" ]; then
    echo "[*] Setting channel to $CHANNEL..."
    iw dev "$IFACE" set channel "$CHANNEL"
fi

sleep 1
if iw dev "$IFACE" info 2>/dev/null | grep -q "type monitor"; then
    echo ""
    echo "[+] Monitor mode enabled on $IFACE"
    echo ""
    echo "    export WIFIGUARD_IFACE=$IFACE"
    echo "    export WIFIGUARD_SIM=false"
    echo ""
    echo "    # Start the backend:"
    echo "    cd backend && python app.py"
else
    echo "[!] Failed to enable monitor mode on $IFACE"
    exit 1
fi
