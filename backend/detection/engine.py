import threading
import time

from config import DETECTION_INTERVAL, SIMULATION_MODE, PCAP_FILE_PATHS, MONITOR_INTERFACE, TARGET_SSID
from services.alert_service import create_alert
from services.device_service import bulk_upsert, upsert_device, remove_stale_devices
from services.whitelist_service import is_whitelisted
from services.email_service import send_alert, get_config
from detection.packet_reader import PacketReader, FC_BEACON, FC_PROBE_RESP
from utils.time_utils import now_str
from utils.oui_db import lookup_vendor


class DetectionEngine:

    def __init__(self):
        self._running = False
        self._thread = None
        self._simulator = None
        self._detectors = []
        self._pcap_frames = []
        self._pcap_frame_index = 0
        self._live_capture = None
        self._target_bssids = set()
        self._tick_live_empty_count = 0
        self._load_detectors()

    def _load_detectors(self):
        from detection.deauth import DeauthDetector
        from detection.evil_twin import EvilTwinDetector
        from detection.flood import FloodDetector
        from detection.brute_force import BruteForceDetector
        from detection.illegal_access import IllegalAccessDetector
        from detection.weak_password import WeakPasswordDetector
        from detection.weak_encryption import WeakEncryptionDetector
        from detection.krack import KrackDetector

        self._detectors = [
            DeauthDetector(),
            EvilTwinDetector(),
            FloodDetector(),
            BruteForceDetector(),
            IllegalAccessDetector(),
            WeakPasswordDetector(),
            WeakEncryptionDetector(),
            KrackDetector(),
        ]

    def start(self):
        pcap_paths = self._get_pcap_paths()

        if pcap_paths:
            print("[*] PCAP回放模式")
            self._load_pcap_frames(pcap_paths)
            self._configure_detectors_for_pcap()
        elif SIMULATION_MODE:
            print("[*] 模拟模式")
            from detection.simulator import SimulatorDataGenerator
            self._simulator = SimulatorDataGenerator()
        else:
            print("[*] 真实监听模式 - 接口: {}".format(MONITOR_INTERFACE))
            try:
                from detection.packet_reader import LivePacketCapture
                self._live_capture = LivePacketCapture(MONITOR_INTERFACE)
                self._live_capture.start()
            except Exception as e:
                print("[!] 启动监听失败: {}".format(e))

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _get_pcap_paths(self):
        if not PCAP_FILE_PATHS:
            return []
        return [p.strip() for p in PCAP_FILE_PATHS.split(",") if p.strip()]

    def _load_pcap_frames(self, pcap_paths):
        for path in pcap_paths:
            try:
                reader = PacketReader(path)
                frames = list(reader.read_frames())
                self._pcap_frames.extend(frames)
            except FileNotFoundError:
                pass

    def _configure_detectors_for_pcap(self):
        ap_macs = set()
        for f in self._pcap_frames:
            if f["frameType"] == FC_BEACON:
                bssid = f.get("bssid", "") or f.get("sa", "")
                if bssid:
                    ap_macs.add(bssid)

        for detector in self._detectors:
            if hasattr(detector, "set_ap_macs"):
                detector.set_ap_macs(ap_macs)

    def stop(self):
        self._running = False
        if self._live_capture:
            self._live_capture.stop()

    def _run_loop(self):
        while self._running:
            try:
                if self._pcap_frames:
                    self._tick_pcap()
                elif self._simulator:
                    self._tick_simulation()
                elif self._live_capture:
                    self._tick_live()
                else:
                    self._tick_detectors_only()

                remove_stale_devices(120)
                time.sleep(DETECTION_INTERVAL)
            except Exception as e:
                print("[!] 检测循环异常: {}".format(e))
                time.sleep(DETECTION_INTERVAL)

    def _extract_devices_from_frames(self, frames):
        if TARGET_SSID:
            for f in frames:
                ft = f["frameType"]
                if ft in (FC_BEACON, FC_PROBE_RESP):
                    ssid = f.get("ssid", "").strip()
                    bssid = f.get("bssid", "") or f.get("sa", "")
                    if ssid == TARGET_SSID and bssid:
                        self._target_bssids.add(bssid)

        do_filter = TARGET_SSID and len(self._target_bssids) > 0
        seen = {}
        now = now_str()
        for f in frames:
            if do_filter:
                frame_bssid = f.get("bssid", "")
                if frame_bssid not in self._target_bssids:
                    continue

            mac = f.get("sa", "")
            bssid = f.get("bssid", "")
            ssid = f.get("ssid", "")
            signal = f.get("signal")
            frame_ip = f.get("ip", "")
            pc = f.get("pairwiseCipher", "")
            gc = f.get("groupCipher", "")
            akm = f.get("akm", "")

            for addr in (mac, bssid):
                if not addr or addr in seen:
                    continue
                if addr == "00:00:00:00:00:00" or addr.startswith("ff:ff:ff:ff"):
                    continue
                status = "正常"
                if signal is not None and signal < -75:
                    status = "可疑"
                vendor = lookup_vendor(addr)
                entry = seen[addr] = seen.get(addr, {
                    "mac": addr,
                    "ip": "",
                    "ssid": "",
                    "signal": signal if signal is not None else -70,
                    "status": status,
                    "vendor": vendor,
                    "pairwiseCipher": pc,
                    "groupCipher": gc,
                    "akm": akm,
                    "first_seen": now,
                    "last_seen": now,
                })
                if ssid and not entry["ssid"]:
                    entry["ssid"] = ssid
                if frame_ip and not entry["ip"]:
                    entry["ip"] = frame_ip
                if pc and not entry["pairwiseCipher"]:
                    entry["pairwiseCipher"] = pc
                if gc and not entry["groupCipher"]:
                    entry["groupCipher"] = gc
                if akm and not entry["akm"]:
                    entry["akm"] = akm
        if seen:
            bulk_upsert(list(seen.values()))

    def _tick_simulation(self):
        devices = self._simulator.tick()
        if TARGET_SSID:
            devices = [d for d in devices if d.get("ssid") == TARGET_SSID]
        bulk_upsert(devices)
        attacks = self._simulator.get_attacks()
        if attacks:
            print("[检测] 仿真模式下检测到攻击: {}".format([a.get("type") for a in attacks]))
        for attack in attacks:
            source = attack.get("sourceMac", attack.get("source_mac", ""))
            if source and is_whitelisted(source):
                print("[检测] 源MAC {} 在白名单中，跳过告警".format(source))
                continue
            create_alert(attack)
            self._maybe_send_email(attack)

    def _tick_pcap(self):
        chunk_size = DETECTION_INTERVAL * 132
        start = self._pcap_frame_index
        end = min(start + chunk_size, len(self._pcap_frames))
        batch = self._pcap_frames[start:end]
        self._pcap_frame_index = end

        if not batch:
            return

        self._extract_devices_from_frames(batch)

        for detector in self._detectors:
            try:
                result = detector.analyze(batch)
                if result:
                    print("[检测] {} 检测到: {}".format(
                        type(detector).__name__, result.get("type")))
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        print("[检测] 源MAC {} 在白名单中，跳过".format(source))
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception as e:
                print("[检测] {} 检测器错误: {}".format(
                    type(detector).__name__, e))

        if self._pcap_frame_index >= len(self._pcap_frames):
            self._pcap_frame_index = 0

    def _tick_detectors_only(self):
        pass

    def _tick_live(self):
        frames = self._live_capture.drain_frames()
        if not frames:
            self._tick_live_empty_count += 1
            if self._tick_live_empty_count == 15:
                print("[!] 已等待30秒未收到数据帧，请确认:")
                print("    1. 网卡 {} 是否已开启monitor模式?".format(MONITOR_INTERFACE))
                print("    2. 运行 sudo ./scripts/setup_monitor.sh {}".format(MONITOR_INTERFACE))
            return

        self._tick_live_empty_count = 0
        print("[*] 收到 {} 个数据帧".format(len(frames)))
        self._extract_devices_from_frames(frames)

        for detector in self._detectors:
            try:
                result = detector.analyze(frames)
                if result:
                    print("[检测] {} 检测到: {}".format(
                        type(detector).__name__, result.get("type")))
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception as e:
                print("[检测] {} 检测器错误: {}".format(
                    type(detector).__name__, e))

    def _maybe_send_email(self, alert):
        try:
            config = get_config()
            if config["enabled"]:
                send_alert(
                    alert_type=alert["type"],
                    severity=alert["severity"],
                    source_mac=str(alert.get("sourceMac", alert.get("source_mac", ""))),
                    target_mac=str(alert.get("targetMac", alert.get("target_mac", ""))),
                    timestamp=alert["timestamp"],
                    suggestion=alert.get("suggestion", ""),
                )
        except Exception as e:
            print(f"[Email] 发送失败: {e}")
