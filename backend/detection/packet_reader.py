import subprocess
import os
import re
import threading
import queue


TSHARK_FIELDS = [
    "wlan.fc.type_subtype",
    "wlan.sa",
    "wlan.da",
    "wlan.bssid",
    "wlan.ssid",
    "frame.time",
    "radiotap.dbm_antsignal",
    "_ws.col.Info",
    "arp.src.proto_ipv4",
    "ip.src",
    "wlan.rsn.gcs.type",
    "wlan.rsn.pcs.type",
    "wlan.rsn.akms.type",
    "wlan.rsn.capabilities.mfpc",
    "wlan.rsn.capabilities.mfpr",
    "wlan.fixed.capabilities.privacy",
    "wlan_radio.channel",
    "wlan_radio.frequency",
]


def _decode_ssid(value):
    if not value:
        return ""
    if re.fullmatch(r"(?:[0-9a-fA-F]{2})+", value):
        try:
            decoded = bytes.fromhex(value).decode("utf-8")
        except UnicodeDecodeError:
            return value
        if decoded.isprintable():
            return decoded
    return value


def _parse_tshark_line(line):
    """Parse a single tshark -T fields output line into a frame dict.

    Returns a dict with keys: frameType, sa, da, bssid, ssid, timestamp,
    signal, info. Returns None if the frame type field cannot be parsed.
    """
    parts = line.split("|")
    raw = dict(zip(TSHARK_FIELDS, parts))

    fc = raw.get("wlan.fc.type_subtype", "")
    sa = raw.get("wlan.sa", "")
    da = raw.get("wlan.da", "")
    bssid = raw.get("wlan.bssid", "")
    ssid = _decode_ssid(raw.get("wlan.ssid", ""))
    timestamp = raw.get("frame.time", "")
    signal = raw.get("radiotap.dbm_antsignal", "")
    info = raw.get("_ws.col.Info", "")

    try:
        fc_int = int(fc, 16)
    except (ValueError, TypeError):
        return None

    arp_ip = raw.get("arp.src.proto_ipv4", "")
    ip_src = raw.get("ip.src", "")

    return {
        "frameType": fc_int,
        "sa": sa.lower(),
        "da": da.lower(),
        "bssid": bssid.lower(),
        "ssid": ssid,
        "timestamp": timestamp,
        "signal": int(signal) if signal else None,
        "info": info,
        "pairwiseCipher": raw.get("wlan.rsn.pcs.type", ""),
        "groupCipher": raw.get("wlan.rsn.gcs.type", ""),
        "akm": raw.get("wlan.rsn.akms.type", ""),
        "pmfCapable": raw.get("wlan.rsn.capabilities.mfpc", ""),
        "pmfRequired": raw.get("wlan.rsn.capabilities.mfpr", ""),
        "privacy": raw.get("wlan.fixed.capabilities.privacy", ""),
        "channel": raw.get("wlan_radio.channel", ""),
        "frequency": raw.get("wlan_radio.frequency", ""),
        "tagInterpretation": raw.get("wlan.tag.interpretation", ""),
        "ip": arp_ip if arp_ip else ip_src,
    }


class PacketReader:
    """Reads 802.11 pcap files via tshark and yields parsed frame dicts."""

    def __init__(self, pcap_path):
        if not os.path.exists(pcap_path):
            raise FileNotFoundError(f"pcap file not found: {pcap_path}")
        self.pcap_path = pcap_path
        self._beacon_info = None

    def read_frames(self):
        """Yield all frames from the pcap as parsed dicts."""
        cmd = [
            "tshark", "-r", self.pcap_path,
            "-T", "fields",
            "-E", "separator=|",
            "-E", "occurrence=f",
        ]
        for f in TSHARK_FIELDS:
            cmd.extend(["-e", f])

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            frame = _parse_tshark_line(line)
            if frame:
                yield frame

        proc.wait()

    def get_beacon_security_info(self):
        """Extract RSN/WPA security info from the first beacon frame.

        Returns a dict with keys: rsn_version, group_cipher, pairwise_cipher,
        akms, has_wpa1, uses_tkip, uses_wep, has_rsn.
        Returns None if no beacon found or parsing failed.
        """
        if self._beacon_info is not None:
            return self._beacon_info

        cmd = [
            "tshark", "-r", self.pcap_path,
            "-Y", "wlan.fc.type_subtype == 0x0008",
            "-V",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError):
            self._beacon_info = None
            return None

        if proc.returncode != 0 or not proc.stdout:
            self._beacon_info = None
            return None

        info = {}
        output = proc.stdout

        # RSN Version
        rsn_ver = re.search(r"RSN Version:\s*(\d+)", output)
        info["rsn_version"] = int(rsn_ver.group(1)) if rsn_ver else None

        # Group Cipher Suite
        grp = re.search(r"Group Cipher Suite(?: type)?:\s*(?:[\da-f:]+ \([^)]+\) )?(\S+)", output)
        info["group_cipher"] = grp.group(1) if grp else None

        # Pairwise Cipher Suite
        pwc = re.search(r"Pairwise Cipher Suite(?: type)?:\s*(?:[\da-f:]+ \([^)]+\) )?(\S+)", output)
        info["pairwise_cipher"] = pwc.group(1) if pwc else None

        # AKM Suite
        akm = re.search(r"AKM(?: Suite)?(?: type)?:\s*(?:[\da-f:]+ \([^)]+\) )?(\S+)", output)
        info["akms"] = akm.group(1) if akm else None

        # Check for WPA (not RSN) - WPA1 uses a vendor-specific IE with WPA tag
        info["has_rsn"] = "RSN Information" in output
        info["has_wpa1"] = not info["has_rsn"] and ("WPA" in output)

        # Determine if using vulnerable encryption
        grp_lower = (info.get("group_cipher") or "").lower()
        pwc_lower = (info.get("pairwise_cipher") or "").lower()
        info["uses_tkip"] = "tkip" in grp_lower or "tkip" in pwc_lower
        info["uses_wep"] = "wep" in grp_lower or "wep" in pwc_lower

        self._beacon_info = info
        return info


def read_pcap_frames(pcap_path):
    """Convenience: read and return all frames from a pcap file."""
    reader = PacketReader(pcap_path)
    return list(reader.read_frames())


# WLAN frame type/subtype constants
FC_ASSOC_REQ = 0x0000
FC_ASSOC_RESP = 0x0001
FC_REASSOC_REQ = 0x0002
FC_REASSOC_RESP = 0x0003
FC_PROBE_REQ = 0x0004
FC_PROBE_RESP = 0x0005
FC_BEACON = 0x0008
FC_DISASSOC = 0x000a
FC_AUTH = 0x000b
FC_DEAUTH = 0x000c

# EAPOL Key Message patterns in Info field
EAPOL_KEY_MSG_1 = "Key (Message 1 of 4)"
EAPOL_KEY_MSG_2 = "Key (Message 2 of 4)"
EAPOL_KEY_MSG_3 = "Key (Message 3 of 4)"
EAPOL_KEY_MSG_4 = "Key (Message 4 of 4)"

# RSN cipher suite types
CIPHER_WEP40 = 1
CIPHER_TKIP = 2
CIPHER_AES_CCMP = 4
CIPHER_WEP104 = 5

AKM_PSK = 2


class LivePacketCapture:
    """Captures 802.11 frames from a live wireless interface using tshark.

    Runs tshark in a background subprocess, reads its stdout in a daemon
    thread, parses each line into a frame dict, and buffers frames in a
    thread-safe queue. The engine calls drain_frames() each tick to
    retrieve all buffered frames.
    """

    def __init__(self, interface):
        self.interface = interface
        self._queue = queue.Queue()
        self._process = None
        self._thread = None
        self._thread2 = None
        self._running = False

    def start(self):
        """Launch tshark and start the background reader thread."""
        import time as _time

        if not self._check_monitor_mode():
            print("[!] 接口 {} 未处于 monitor 模式，请执行:".format(self.interface))
            print("    sudo airmon-ng check kill")
            print("    sudo airmon-ng start {}".format(self.interface))
            print("    然后将 WIFIGUARD_IFACE 设置为新接口名 (通常为 {}mon)".format(self.interface))
            print("    或运行: sudo ./scripts/setup_monitor.sh {}".format(self.interface))
            print("")

        cmd = [
            "tshark", "-i", self.interface,
            "-l",
            "-T", "fields",
            "-E", "separator=|",
            "-E", "occurrence=f",
        ]
        for f in TSHARK_FIELDS:
            cmd.extend(["-e", f])

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        self._thread2 = threading.Thread(target=self._stderr_loop, daemon=True)
        self._thread2.start()
        self._first_frame_time = _time.time()
        print("[+] 监听已启动，等待数据帧... (接口: {})".format(self.interface))

    def _check_monitor_mode(self):
        """Check if the interface is in monitor mode. Returns True if yes."""
        try:
            import subprocess as _sp
            r = _sp.run(
                ["iw", "dev", self.interface, "info"],
                capture_output=True, text=True, timeout=5
            )
            return "type monitor" in r.stdout.lower()
        except Exception:
            return False

    def _read_loop(self):
        """Continuously read lines from tshark stdout and enqueue parsed frames."""
        try:
            for line in self._process.stdout:
                if not self._running:
                    break
                line = line.strip()
                if not line:
                    continue
                frame = _parse_tshark_line(line)
                if frame:
                    self._queue.put(frame)
                    print("*", end="", flush=True)
            if self._running:
                print("[!] tshark 进程已退出，检查上方的 [tshark] 错误信息")
        except Exception as e:
            print("[!] 监听读取线程异常: {}".format(e))

    def _stderr_loop(self):
        """Read tshark stderr for diagnostics."""
        try:
            for line in self._process.stderr:
                if not self._running:
                    break
                line = line.strip()
                if line:
                    print("[tshark] {}".format(line))
        except Exception:
            pass

    def drain_frames(self):
        """Return all buffered frames as a list. Non-blocking."""
        frames = []
        while True:
            try:
                frames.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return frames

    def stop(self):
        """Stop the capture subprocess and clean up."""
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
        ret = self._process.poll() if self._process else -1
        if ret and ret != -15:
            print("[!] tshark 退出码: {}".format(ret))
