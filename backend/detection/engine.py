import threading
import time

from config import DETECTION_INTERVAL, SIMULATION_MODE
from services.alert_service import create_alert
from services.device_service import bulk_upsert, remove_stale_devices
from services.whitelist_service import is_whitelisted
from services.email_service import send_alert, get_config


class DetectionEngine:

    def __init__(self):
        self._running = False
        self._thread = None
        self._simulator = None
        self._detectors = []
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
        if SIMULATION_MODE:
            from detection.simulator import SimulatorDataGenerator

            self._simulator = SimulatorDataGenerator()

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run_loop(self):
        while self._running:
            try:
                if self._simulator:
                    devices = self._simulator.tick()
                    bulk_upsert(devices)
                    attacks = self._simulator.get_attacks()
                    for attack in attacks:
                        source = attack.get("sourceMac", attack.get("source_mac", ""))
                        if source and is_whitelisted(source):
                            continue
                        create_alert(attack)
                        self._maybe_send_email(attack)
                else:
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
                    except Exception as e:
                        pass

                remove_stale_devices(120)

                time.sleep(DETECTION_INTERVAL)
            except Exception:
                time.sleep(DETECTION_INTERVAL)

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
        except Exception:
            pass
