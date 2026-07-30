#!/usr/bin/env python3
"""
WiFiGuard 树莓派部署助手

首次部署:  sudo python3 start.py → 选 [D]
日常启动:  sudo python3 start.py → 选 [A] 或直接 sudo python3 start.py --auto
"""

import os
import sys
import subprocess
import json
import signal
import time
import atexit

# ── 颜色 ──────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── 路径 ──────────────────────────────────────────────

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
CONFIG_FILE = os.path.join(PROJECT_DIR, ".deploy_config.json")

# ── 默认配置 ──────────────────────────────────────────

def _detect_python():
    """优先使用 conda web 环境，其次 SUDO_USER 的 conda，最后系统 Python"""
    # 直接检测已知的 conda 环境
    sudo_user = os.environ.get("SUDO_USER", "")
    candidates = []
    if sudo_user:
        candidates.append(f"/home/{sudo_user}/miniconda3/envs/web/bin/python")
        candidates.append(f"/home/{sudo_user}/anaconda3/envs/web/bin/python")
    candidates.append(os.path.expanduser("~/miniconda3/envs/web/bin/python"))
    candidates.append(os.path.expanduser("~/anaconda3/envs/web/bin/python"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return sys.executable

DEFAULT_CONFIG = {
    "AP_IF": "wlan0",
    "MON_IF": "wlan1",
    "MGMT_IF": "eth0",
    "UPLINK_IF": "usb0",
    "AP_IP": "10.77.0.1",
    "MGMT_IP": "10.99.0.1",
    "AP_SSID": "WIFIGuard-Lab",
    "AP_PASS": "WIFIGuard2026",
    "AP_CHANNEL": "6",
    "DHCP_START": "10.77.0.100",
    "DHCP_END": "10.77.0.199",
    "PYTHON_BIN": _detect_python(),
}

# ── 进程追踪 ──────────────────────────────────────────

CHILD_PROCS = []

# ── 工具函数 ──────────────────────────────────────────

def banner():
    print(f"""{CYAN}{BOLD}
╔══════════════════════════════════════════╗
║      WiFiGuard 树莓派部署助手            ║
╚══════════════════════════════════════════╝{RESET}
""")

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def err(msg):
    print(f"  {RED}✗{RESET} {msg}")

def info(msg):
    print(f"  {CYAN}→{RESET} {msg}")

def header(title):
    print(f"\n{BOLD}{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}{RESET}")

def run(cmd, shell=False, timeout=30):
    """运行命令，返回 (success, stdout, stderr)"""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            shell=shell, timeout=timeout
        )
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "超时"
    except Exception as e:
        return False, "", str(e)

def run_show(cmd, shell=False, timeout=60):
    """运行命令并直接显示输出"""
    try:
        subprocess.run(cmd, shell=shell, timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        err("命令超时")
        return False
    except Exception as e:
        err(str(e))
        return False

def get_input(prompt, default=""):
    try:
        if default:
            r = input(f"  {prompt} [{CYAN}{default}{RESET}]: ").strip()
            return r if r else default
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

def wait_enter(msg="按 Enter 继续..."):
    try:
        input(f"  {msg}")
    except (EOFError, KeyboardInterrupt):
        print()

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            cfg = dict(DEFAULT_CONFIG)
            cfg.update(saved)
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def cleanup():
    """退出时清理子进程"""
    for p in CHILD_PROCS:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

atexit.register(cleanup)

# ══════════════════════════════════════════════════════
#  阶段 1: 检查环境
# ══════════════════════════════════════════════════════

def stage_check_env():
    header("1. 检查系统环境")

    if os.geteuid() != 0:
        err("需要 root 权限，请使用: sudo python3 start.py")
        return False
    ok("root 权限")

    # 架构
    success, arch, _ = run(["uname", "-m"])
    ok(f"架构: {arch}")

    # 系统包
    required = ["hostapd", "dnsmasq-base", "nftables", "tshark", "iw"]
    missing = []
    for pkg in required:
        ret, _, _ = run(["dpkg", "-s", pkg])
        if not ret:
            missing.append(pkg)

    if missing:
        warn(f"缺少: {', '.join(missing)}")
        if confirm("自动安装?"):
            # tshark 非交互配置
            subprocess.run(
                ["bash", "-c",
                 'echo "wireshark-common wireshark-common/install-setuid boolean true"'
                 " | debconf-set-selections"],
                capture_output=True
            )
            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"
            ret = subprocess.run(
                ["apt-get", "install", "-y"] + missing,
                env=env
            )
            if ret.returncode == 0:
                ok("系统包安装完成")
            else:
                err("安装失败，请手动 apt install")
                return False
        else:
            err("请先安装缺失的包")
            return False
    else:
        ok(f"系统包完整 ({len(required)} 个)")

    # Python
    success, pyver, _ = run([sys.executable, "--version"])
    ok(f"Python: {pyver}")

    # Node/npm
    success, ver, _ = run(["node", "--version"])
    if success:
        ok(f"Node.js: {ver}")
    else:
        warn("未检测到 Node.js (前端需要)")

    success, ver, _ = run(["npm", "--version"])
    if success:
        ok(f"npm: {ver}")
    else:
        warn("未检测到 npm")

    # 检测无线网卡
    print()
    success, iw_out, _ = run(["iw", "dev"])
    if success:
        ifaces = [l.split()[1] for l in iw_out.splitlines() if "Interface" in l]
        if ifaces:
            ok(f"无线网卡: {', '.join(ifaces)}")
        else:
            warn("未检测到无线网卡")
    return True


# ══════════════════════════════════════════════════════
#  阶段 2: 配置网络参数
# ══════════════════════════════════════════════════════

def stage_configure(cfg):
    header("2. 网络参数配置")
    print()

    cfg["AP_IF"] = get_input("AP 接口 (内置WiFi)", cfg["AP_IF"])
    cfg["MON_IF"] = get_input("Monitor 接口 (USB网卡)", cfg["MON_IF"])
    cfg["MGMT_IF"] = get_input("管理接口 (网线直连)", cfg["MGMT_IF"])
    cfg["UPLINK_IF"] = get_input("上行接口 (手机共享)", cfg["UPLINK_IF"])
    print()
    cfg["AP_SSID"] = get_input("WiFi 名称", cfg["AP_SSID"])
    cfg["AP_PASS"] = get_input("WiFi 密码", cfg["AP_PASS"])
    cfg["AP_CHANNEL"] = get_input("WiFi 信道", cfg["AP_CHANNEL"])
    print()
    cfg["AP_IP"] = get_input("AP 网关", cfg["AP_IP"])
    cfg["DHCP_START"] = get_input("DHCP 起始", cfg["DHCP_START"])
    cfg["DHCP_END"] = get_input("DHCP 结束", cfg["DHCP_END"])
    cfg["MGMT_IP"] = get_input("管理口 IP", cfg["MGMT_IP"])
    print()
    cfg["PYTHON_BIN"] = get_input("Python 路径", cfg["PYTHON_BIN"])

    save_config(cfg)
    ok("配置已保存")

    print(f"\n  {BOLD}网络拓扑:{RESET}")
    print(f"    ┌─ {cfg['AP_IF']}  → AP ({cfg['AP_SSID']}) {cfg['AP_IP']}/24")
    print(f"    ├─ {cfg['MON_IF']} → Monitor (CH{cfg['AP_CHANNEL']})")
    print(f"    ├─ {cfg['MGMT_IF']}  → 管理 {cfg['MGMT_IP']}/24")
    print(f"    └─ {cfg['UPLINK_IF']}  → 上行 (NAT)")
    return True


# ══════════════════════════════════════════════════════
#  阶段 3: 安装系统配置文件
# ══════════════════════════════════════════════════════

def stage_install_configs(cfg):
    header("3. 安装系统配置文件")

    # hostapd
    hostapd_conf = f"""# WiFiGuard AP - 由 start.py 生成
interface={cfg['AP_IF']}
driver=nl80211
ssid={cfg['AP_SSID']}
country_code=CN
hw_mode=g
channel={cfg['AP_CHANNEL']}
ieee80211n=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase={cfg['AP_PASS']}
ieee80211w=1
wmm_enabled=1
ctrl_interface=/var/run/hostapd
ctrl_interface_group=0
"""
    os.makedirs("/etc/hostapd", exist_ok=True)
    with open("/etc/hostapd/wifiguard.conf", "w") as f:
        f.write(hostapd_conf)
    ok("hostapd: /etc/hostapd/wifiguard.conf")

    # dnsmasq
    dnsmasq_conf = f"""# WiFiGuard DHCP/DNS - 由 start.py 生成
interface={cfg['AP_IF']}
bind-dynamic
dhcp-range={cfg['DHCP_START']},{cfg['DHCP_END']},255.255.255.0,12h
dhcp-option=3,{cfg['AP_IP']}
dhcp-option=6,{cfg['AP_IP']}
domain=wifiguard.lab
address=/portal.wifiguard.lab/{cfg['AP_IP']}
log-dhcp
"""
    os.makedirs("/etc/dnsmasq.d", exist_ok=True)
    with open("/etc/dnsmasq.d/wifiguard.conf", "w") as f:
        f.write(dnsmasq_conf)
    ok("dnsmasq: /etc/dnsmasq.d/wifiguard.conf")

    # nftables
    nft_conf = f"""#!/usr/sbin/nft -f
# WiFiGuard 防火墙 - 由 start.py 生成
flush ruleset

table inet wifiguard {{
    set trusted_macs {{ type ether_addr; }}
    set blocked_macs {{ type ether_addr; }}

    chain input {{
        type filter hook input priority filter; policy accept;
        iifname "lo" accept
        ct state established,related accept
        iifname "{cfg['AP_IF']}" udp dport {{ 53, 67 }} accept
        iifname "{cfg['AP_IF']}" tcp dport {{ 53, 80, 8000 }} accept
        iifname "{cfg['MGMT_IF']}" accept
        iifname "{cfg['UPLINK_IF']}" accept
    }}

    chain forward {{
        type filter hook forward priority filter; policy drop;
        iifname "{cfg['AP_IF']}" ether saddr @blocked_macs drop
        oifname "{cfg['AP_IF']}" ether daddr @blocked_macs drop
        ct state established,related accept
        iifname "{cfg['AP_IF']}" ether saddr @trusted_macs oifname "{cfg['UPLINK_IF']}" accept
    }}
}}

table ip wifiguard_nat {{
    chain postrouting {{
        type nat hook postrouting priority srcnat;
        oifname "{cfg['UPLINK_IF']}" ip saddr {cfg['AP_IP'].rsplit('.', 1)[0]}.0/24 masquerade
    }}
}}
"""
    os.makedirs("/etc/nftables.d", exist_ok=True)
    with open("/etc/nftables.d/wifiguard.nft", "w") as f:
        f.write(nft_conf)
    ok("nftables: /etc/nftables.d/wifiguard.nft")

    # sysctl
    with open("/etc/sysctl.d/99-wifiguard.conf", "w") as f:
        f.write("net.ipv4.ip_forward=1\n")
    ok("sysctl: IP 转发")

    # NetworkManager unmanage
    os.makedirs("/etc/NetworkManager/conf.d", exist_ok=True)
    with open("/etc/NetworkManager/conf.d/wifiguard.conf", "w") as f:
        f.write(f"[keyfile]\nunmanaged-devices=interface-name:{cfg['AP_IF']}\n")
    ok("NetworkManager: 放开 AP 接口")

    # 确保 dnsmasq 主配置加载 conf-dir
    dnsmasq_main = "/etc/dnsmasq.conf"
    if os.path.exists(dnsmasq_main):
        with open(dnsmasq_main) as f:
            content = f.read()
        if "conf-dir=/etc/dnsmasq.d" not in content:
            with open(dnsmasq_main, "a") as f:
                f.write("\nconf-dir=/etc/dnsmasq.d/,*.conf\n")
            ok("dnsmasq.conf: 添加 conf-dir")
    else:
        with open(dnsmasq_main, "w") as f:
            f.write("conf-dir=/etc/dnsmasq.d/,*.conf\n")
        ok("dnsmasq.conf: 创建")

    return True


# ══════════════════════════════════════════════════════
#  阶段 4: 配置网卡
# ══════════════════════════════════════════════════════

def stage_setup_network(cfg):
    header("4. 配置网络接口")

    ap_if = cfg["AP_IF"]
    mon_if = cfg["MON_IF"]
    mgmt_if = cfg["MGMT_IF"]
    ap_ip = cfg["AP_IP"]
    mgmt_ip = cfg["MGMT_IP"]
    channel = cfg["AP_CHANNEL"]

    # IP forwarding
    run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    ok("IP 转发已开启")

    # NetworkManager release
    run(["nmcli", "device", "set", ap_if, "managed", "no"])
    ok(f"NetworkManager 放开 {ap_if}")

    # AP interface
    run(["ip", "link", "set", ap_if, "down"])
    run(["ip", "addr", "flush", "dev", ap_if])
    run(["ip", "addr", "add", f"{ap_ip}/24", "dev", ap_if])
    run(["ip", "link", "set", ap_if, "up"])
    ok(f"{ap_if}: {ap_ip}/24")

    # Management interface
    run(["ip", "addr", "flush", "dev", mgmt_if])
    run(["ip", "addr", "add", f"{mgmt_ip}/24", "dev", mgmt_if])
    run(["ip", "link", "set", mgmt_if, "up"])
    ok(f"{mgmt_if}: {mgmt_ip}/24")

    # Monitor interface
    run(["ip", "link", "set", mon_if, "down"])
    success, _, error = run(["iw", "dev", mon_if, "set", "type", "monitor"])
    if not success:
        warn(f"Monitor 设置失败: {error}")
        warn(f"USB网卡 {mon_if} 可能未插入，插入后重新执行此步骤")
    else:
        run(["ip", "link", "set", mon_if, "up"])
        run(["iw", "dev", mon_if, "set", "channel", channel])
        ok(f"{mon_if}: monitor 模式, CH{channel}")

    return True


# ══════════════════════════════════════════════════════
#  阶段 5: 启动基础服务
# ══════════════════════════════════════════════════════

def stage_start_services(cfg):
    header("5. 启动基础服务")

    ap_if = cfg["AP_IF"]

    # 停止系统自带的可能冲突的服务
    run(["systemctl", "stop", "hostapd"])
    run(["systemctl", "stop", "dnsmasq"])

    # 杀掉旧进程
    run(["pkill", "-f", "hostapd.*wifiguard"])
    run(["pkill", "-f", "dnsmasq.*wifiguard"])
    time.sleep(1)

    # nftables
    success, _, error = run(["nft", "-f", "/etc/nftables.d/wifiguard.nft"])
    if success:
        ok("nftables 规则已加载")
    else:
        err(f"nftables 失败: {error}")

    # hostapd
    info("启动 hostapd...")
    hostapd_proc = subprocess.Popen(
        ["/usr/sbin/hostapd", "/etc/hostapd/wifiguard.conf"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True
    )
    time.sleep(2)
    if hostapd_proc.poll() is not None:
        out = hostapd_proc.stdout.read().decode()
        err(f"hostapd 启动失败:\n{out}")
        return False
    CHILD_PROCS.append(hostapd_proc)
    ok(f"hostapd (PID {hostapd_proc.pid})")

    # dnsmasq
    info("启动 dnsmasq...")
    dnsmasq_proc = subprocess.Popen(
        ["/usr/sbin/dnsmasq", "-C", "/etc/dnsmasq.d/wifiguard.conf",
         "--no-daemon", "--log-facility=-"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True
    )
    time.sleep(1)
    if dnsmasq_proc.poll() is not None:
        out = dnsmasq_proc.stdout.read().decode()
        err(f"dnsmasq 启动失败:\n{out}")
        return False
    CHILD_PROCS.append(dnsmasq_proc)
    ok(f"dnsmasq (PID {dnsmasq_proc.pid})")

    return True


# ══════════════════════════════════════════════════════
#  阶段 6: 安装项目依赖
# ══════════════════════════════════════════════════════

def stage_install_deps(cfg):
    header("6. 安装项目依赖")

    python_bin = cfg["PYTHON_BIN"]
    pip_bin = os.path.join(os.path.dirname(python_bin), "pip")
    if not os.path.exists(pip_bin):
        pip_bin = f"{python_bin} -m pip"

    # Backend
    req_file = os.path.join(BACKEND_DIR, "requirements.txt")
    if os.path.exists(req_file):
        info("安装 Python 依赖...")
        if os.path.exists(pip_bin):
            ret = subprocess.run([pip_bin, "install", "-r", req_file])
        else:
            ret = subprocess.run(
                [python_bin, "-m", "pip", "install", "-r", req_file]
            )
        if ret.returncode == 0:
            ok("Python 依赖安装完成")
        else:
            warn("部分 Python 依赖安装失败，请手动检查")
    else:
        warn("未找到 requirements.txt")

    # Frontend
    pkg_json = os.path.join(FRONTEND_DIR, "package.json")
    if os.path.exists(pkg_json):
        info("安装前端依赖 (npm install)...")
        ret = subprocess.run(["npm", "install"], cwd=FRONTEND_DIR)
        if ret.returncode == 0:
            ok("前端依赖安装完成")
        else:
            warn("npm install 失败，请手动检查")
    else:
        warn("未找到 frontend/package.json")

    return True


# ══════════════════════════════════════════════════════
#  阶段 7: 启动项目
# ══════════════════════════════════════════════════════

def stage_start_project(cfg):
    header("7. 启动项目")

    python_bin = cfg["PYTHON_BIN"]
    ap_if = cfg["AP_IF"]
    mon_if = cfg["MON_IF"]
    ap_ssid = cfg["AP_SSID"]

    # 杀旧进程
    run(["pkill", "-f", "python.*app.py"])
    time.sleep(1)

    # 后端环境变量
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/usr/sbin:/usr/local/bin:/bin:/sbin:" + env.get("PATH", "")
    env["WIFIGUARD_SIM"] = "false"
    env["WIFIGUARD_IFACE"] = mon_if
    env["WIFIGUARD_NAME"] = ap_ssid

    # 启动后端
    info("启动后端 (Flask + 检测引擎)...")
    backend_proc = subprocess.Popen(
        [python_bin, "app.py"],
        cwd=BACKEND_DIR, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True
    )
    CHILD_PROCS.append(backend_proc)
    time.sleep(3)
    if backend_proc.poll() is not None:
        out = backend_proc.stdout.read().decode()
        err(f"后端启动失败:\n{out}")
        return False
    ok(f"后端已启动 (PID {backend_proc.pid}, 端口 8000)")

    # 启动前端
    info("启动前端 (Vite dev server)...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True
    )
    CHILD_PROCS.append(frontend_proc)
    time.sleep(3)
    if frontend_proc.poll() is not None:
        out = frontend_proc.stdout.read().decode()
        err(f"前端启动失败:\n{out}")
        return False
    ok(f"前端已启动 (PID {frontend_proc.pid}, 端口 3000)")

    # 打印访问信息
    mgmt_ip = cfg["MGMT_IP"]
    print(f"""
{GREEN}{BOLD}  ══════════════════════════════════════════
  ✓ WiFiGuard 启动成功!
  ══════════════════════════════════════════{RESET}

  管理页面: {CYAN}http://{mgmt_ip}:3000{RESET}
  WiFi 热点: {CYAN}{ap_ssid}{RESET} (密码: {ap_ssid and cfg['AP_PASS']})
  后端 API:  http://{mgmt_ip}:8000/api/

  {YELLOW}按 Ctrl+C 停止所有服务{RESET}
""")
    return True


# ══════════════════════════════════════════════════════
#  主菜单
# ══════════════════════════════════════════════════════

def show_config_summary(cfg):
    """显示当前配置摘要"""
    print(f"\n  {BOLD}当前配置:{RESET}")
    print(f"    AP 接口:    {CYAN}{cfg['AP_IF']}{RESET}")
    print(f"    Monitor:    {CYAN}{cfg['MON_IF']}{RESET}")
    print(f"    管理口:     {CYAN}{cfg['MGMT_IF']}{RESET}")
    print(f"    上行口:     {CYAN}{cfg['UPLINK_IF']}{RESET}")
    print(f"    WiFi 名称:  {CYAN}{cfg['AP_SSID']}{RESET}")
    print(f"    WiFi 密码:  {CYAN}{cfg['AP_PASS']}{RESET}")
    print(f"    信道:       {CYAN}{cfg['AP_CHANNEL']}{RESET}")
    print(f"    AP 网关:    {CYAN}{cfg['AP_IP']}{RESET}")
    print(f"    Python:     {CYAN}{cfg['PYTHON_BIN']}{RESET}")
    print()


def stage_quick_edit(cfg):
    """快速修改单项配置"""
    fields = [
        ("1", "AP_IF",      "AP 接口"),
        ("2", "MON_IF",     "Monitor 接口"),
        ("3", "MGMT_IF",    "管理接口"),
        ("4", "UPLINK_IF",  "上行接口"),
        ("5", "AP_SSID",    "WiFi 名称"),
        ("6", "AP_PASS",    "WiFi 密码"),
        ("7", "AP_CHANNEL", "信道"),
        ("8", "AP_IP",      "AP 网关"),
        ("9", "PYTHON_BIN", "Python 路径"),
    ]
    while True:
        header("快速修改配置")
        for num, key, label in fields:
            print(f"    [{num}] {label}: {CYAN}{cfg[key]}{RESET}")
        print(f"\n    [0] 返回")
        print()
        ch = get_input("选择要修改的项").strip()
        if ch == "0" or ch == "":
            break
        matched = [f for f in fields if f[0] == ch]
        if matched:
            _, key, label = matched[0]
            new_val = get_input(f"新的 {label}", cfg[key])
            if new_val != cfg[key]:
                cfg[key] = new_val
                save_config(cfg)
                ok(f"{label} → {new_val}")
        else:
            err("无效选项")


def main():
    cfg = load_config()

    # --auto 参数: 直接全自动启动
    if len(sys.argv) > 1 and sys.argv[1] in ("--auto", "-a"):
        banner()
        print(f"  {BOLD}全自动启动模式{RESET}\n")
        show_config_summary(cfg)
        stage_setup_network(cfg)
        stage_start_services(cfg)
        stage_start_project(cfg)
        wait_forever()
        return

    while True:
        banner()
        show_config_summary(cfg)
        print(f"  {BOLD}阶段列表:{RESET}")
        print(f"    [1] 检查环境")
        print(f"    [2] 配置网络参数 (全部重新配置)")
        print(f"    [3] 安装系统配置 (→ /etc)")
        print(f"    [4] 配置网卡 (IP + Monitor)")
        print(f"    [5] 启动基础服务 (hostapd/dnsmasq/nftables)")
        print(f"    [6] 安装项目依赖 (pip + npm)")
        print(f"    [7] 启动项目 (后端 + 前端)")
        print()
        print(f"    {GREEN}[A] 全自动启动 (4→5→7){RESET}  ← 日常开机")
        print(f"    {CYAN}[D] 首次完整部署 (1→2→3→4→5→6→7){RESET}")
        print(f"    {YELLOW}[C] 快速修改配置{RESET}  ← 改单项参数")
        print(f"    [Q] 退出")
        print()

        choice = get_input("选择").strip().upper()

        if choice == "Q":
            break
        elif choice == "1":
            stage_check_env()
            wait_enter()
        elif choice == "2":
            stage_configure(cfg)
            wait_enter()
        elif choice == "3":
            stage_install_configs(cfg)
            wait_enter()
        elif choice == "4":
            stage_setup_network(cfg)
            wait_enter()
        elif choice == "5":
            stage_start_services(cfg)
            wait_enter()
        elif choice == "6":
            stage_install_deps(cfg)
            wait_enter()
        elif choice == "7":
            stage_start_project(cfg)
            wait_forever()
            break
        elif choice == "C":
            stage_quick_edit(cfg)
        elif choice == "A":
            show_config_summary(cfg)
            if not confirm("使用以上配置启动?"):
                stage_quick_edit(cfg)
                show_config_summary(cfg)
                if not confirm("确认启动?"):
                    continue
                # 用户改了参数，需要重新生成系统配置文件
                stage_install_configs(cfg)
            stage_setup_network(cfg)
            stage_start_services(cfg)
            stage_start_project(cfg)
            wait_forever()
            break
        elif choice == "D":
            if not stage_check_env():
                wait_enter()
                continue
            stage_configure(cfg)
            stage_install_configs(cfg)
            stage_setup_network(cfg)
            stage_start_services(cfg)
            stage_install_deps(cfg)
            stage_start_project(cfg)
            wait_forever()
            break
        else:
            err("无效选项")
            time.sleep(1)


def wait_forever():
    """阻塞等待 Ctrl+C"""
    try:
        while True:
            time.sleep(1)
            # 检查子进程是否意外退出
            for p in CHILD_PROCS:
                if p.poll() is not None:
                    warn(f"进程 {p.pid} 已退出 (code={p.returncode})")
                    CHILD_PROCS.remove(p)
                    break
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}正在停止所有服务...{RESET}")
        cleanup()
        print(f"  {GREEN}已退出{RESET}\n")


if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}请使用 sudo 运行: sudo python3 start.py{RESET}")
        sys.exit(1)
    try:
        main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}用户退出{RESET}")
        cleanup()
