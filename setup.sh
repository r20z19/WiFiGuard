#!/usr/bin/env python3
"""
WiFiGuard 一键部署脚本

在全新树莓派上 git clone 项目、安装好基础依赖后，运行:
    sudo python3 setup.sh

交互式配置所有环境，完成后:
    - 后端: cd backend && python app.py
    - 前端: cd frontend && npm run dev
"""

import os
import sys
import subprocess
import json
import time

# ── 颜色 ──────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── 默认配置 ──────────────────────────────────────────

DEFAULT_CONFIG = {
    "AP_IF": "wlan0",
    "MON_IF": "wlan1",
    "MGMT_IF": "eth0",
    "UPLINK_IF": "usb0",
    "AP_IP": "10.77.0.1",
    "AP_SUBNET": "24",
    "MGMT_IP": "10.99.0.1",
    "MGMT_SUBNET": "24",
    "AP_SSID": "WIFIGuard-Lab",
    "AP_PASS": "WIFIGuard2026",
    "AP_CHANNEL": "6",
    "DHCP_START": "10.77.0.100",
    "DHCP_END": "10.77.0.199",
    "BACKEND_PORT": "8000",
    "FRONTEND_PORT": "3000",
}

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, ".deploy_config.json")

# ── 工具函数 ──────────────────────────────────────────

def banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════╗
║       WiFiGuard 树莓派部署助手                   ║
╚══════════════════════════════════════════════════╝{RESET}
""")

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def err(msg):
    print(f"  {RED}✗{RESET} {msg}")

def info(msg):
    print(f"  {CYAN}→{RESET} {msg}")

def header(msg):
    print(f"\n{BOLD}{'─'*50}")
    print(f"  {msg}")
    print(f"{'─'*50}{RESET}")

def run(cmd, check=False, capture=True, shell=False):
    try:
        r = subprocess.run(
            cmd, capture_output=capture, text=True,
            shell=shell, timeout=30
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)

def run_or_fail(cmd, msg=""):
    success, out, error = run(cmd)
    if not success:
        err(f"{msg}: {error}")
    return success

def get_input(prompt, default=""):
    try:
        if default:
            r = input(f"  {prompt} [{CYAN}{default}{RESET}]: ").strip()
            return r if r else default
        else:
            return input(f"  {prompt}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

def confirm(prompt, default_yes=True):
    suffix = "[Y/n]" if default_yes else "[y/N]"
    try:
        r = input(f"  {prompt} {suffix} ").strip().lower()
        if not r:
            return default_yes
        return r in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)

# ── PLACEHOLDER_CONTINUE ──
