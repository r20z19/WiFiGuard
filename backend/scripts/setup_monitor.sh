#!/bin/bash
# setup_monitor.sh - Put a wireless interface into monitor mode for WiFiGuard
#
# Usage: sudo ./setup_monitor.sh [interface]
# Default interface: wlp0s20f0u1
#
# This script:
#   1. Takes the interface down
#   2. Switches it to monitor mode
#   3. Brings it back up
#   4. Verifies monitor mode is active
#   5. Prints the env vars to set for WiFiGuard
#
# Alternative: use airmon-ng (renames interface to wlan1mon):
#   sudo airmon-ng check kill
#   sudo airmon-ng start wlp0s20f0u1

set -e

IFACE="${1:-wlp0s20f0u1}"

echo "[*] Setting up monitor mode on $IFACE..."

if ! iw dev "$IFACE" info &>/dev/null; then
    echo "[!] Interface $IFACE not found. Available interfaces:"
    iw dev 2>/dev/null | grep Interface | awk '{print "    " $2}'
    exit 1
fi

if iw dev "$IFACE" info 2>/dev/null | grep -q "type monitor"; then
    echo "[*] $IFACE is already in monitor mode"
else
    echo "[*] Bringing $IFACE down..."
    ip link set "$IFACE" down

    echo "[*] Setting type to monitor..."
    iw dev "$IFACE" set type monitor

    echo "[*] Bringing $IFACE up..."
    ip link set "$IFACE" up
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
