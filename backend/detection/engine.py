import threading
import time

from config import DETECTION_INTERVAL, SIMULATION_MODE, PCAP_FILE_PATHS
from services.alert_service import create_alert
from services.device_service import bulk_upsert, remove_stale_devices
from services.whitelist_service import is_whitelisted
from services.email_service import send_alert, get_config
from detection.packet_reader import PacketReader, FC_BEACON


class DetectionEngine:

    def __init__(self):
        self._running = False
        self._thread = None
        self._simulator = None
        self._detectors = []
        self._pcap_frames = []
        self._pcap_frame_index = 0
        self._load_detectors()

    def _load_detectors(self):
        from detection.deauth import DeauthDetector
        from detection.evil_twin import EvilTwinDetector
        from detection.flood import FloodDetector
        from detection.brute_force import BruteForceDetector
        from detection.illegal_access import IllegalAccessDetector
        from detection.weak_password import WeakPasswordDetector
        from detection.krack import KrackDetector

        self._detectors = [
            DeauthDetector(),
            EvilTwinDetector(),
            FloodDetector(),
            BruteForceDetector(),
            IllegalAccessDetector(),
            WeakPasswordDetector(),
            KrackDetector(),
        ]

    def start(self):
        pcap_paths = self._get_pcap_paths()

        if pcap_paths:
            self._load_pcap_frames(pcap_paths)
            self._configure_detectors_for_pcap()
        elif SIMULATION_MODE:
            from detection.simulator import SimulatorDataGenerator
            self._simulator = SimulatorDataGenerator()

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
        """Discover AP MACs from beacon frames and configure detectors."""
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

    def _run_loop(self):
        while self._running:
            try:
                if self._pcap_frames:
                    self._tick_pcap()
                elif self._simulator:
                    self._tick_simulation()
                else:
                    self._tick_detectors_only()

                remove_stale_devices(120)
                time.sleep(DETECTION_INTERVAL)
            except Exception:
                time.sleep(DETECTION_INTERVAL)

    def _tick_simulation(self):
        devices = self._simulator.tick()
        bulk_upsert(devices)
        attacks = self._simulator.get_attacks()
        for attack in attacks:
            source = attack.get("sourceMac", attack.get("source_mac", ""))
            if source and is_whitelisted(source):
                continue
            create_alert(attack)
            self._maybe_send_email(attack)

    def _tick_pcap(self):
        """Feed a batch of pcap frames to detectors each tick."""
        chunk_size = DETECTION_INTERVAL * 132  # ~132 packets/sec average rate
        start = self._pcap_frame_index
        end = min(start + chunk_size, len(self._pcap_frames))
        batch = self._pcap_frames[start:end]
        self._pcap_frame_index = end

        if not batch:
            return

        for detector in self._detectors:
            try:
                result = detector.analyze(batch)
                if result:
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception:
                pass

        if self._pcap_frame_index >= len(self._pcap_frames):
            self._pcap_frame_index = 0

    def _tick_detectors_only(self):
        """Run detectors on live device data (no pcap, no simulator)."""
        from services.device_service import get_online_devices
        devices = get_online_devices()

        for detector in self._detectors:
            try:
                result = detector.analyze(devices)
                if result:
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception:
                pass

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
