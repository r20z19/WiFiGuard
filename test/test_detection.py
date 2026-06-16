"""Test detection module against real pcap captures.

Usage:
    conda run -n wifiguard python test/test_detection.py
    conda run -n wifiguard python test/test_detection.py --pcap test/testcase/global-01.cap
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from detection.packet_reader import (
    PacketReader, FC_DEAUTH, FC_AUTH, FC_BEACON, FC_PROBE_RESP,
    FC_ASSOC_REQ, FC_PROBE_REQ, FC_DISASSOC,
    EAPOL_KEY_MSG_1, EAPOL_KEY_MSG_2, EAPOL_KEY_MSG_3, EAPOL_KEY_MSG_4,
)
from detection.deauth import DeauthDetector
from detection.flood import FloodDetector
from detection.brute_force import BruteForceDetector
from detection.evil_twin import EvilTwinDetector
from detection.illegal_access import IllegalAccessDetector
from detection.weak_password import WeakPasswordDetector
from detection.krack import KrackDetector


def analyze_pcap(pcap_path):
    reader = PacketReader(pcap_path)
    frames = list(reader.read_frames())
    print(f"文件: {pcap_path}")
    print(f"总帧数: {len(frames)}")

    # Stats
    deauth = sum(1 for f in frames if f["frameType"] == FC_DEAUTH)
    auth = sum(1 for f in frames if f["frameType"] == FC_AUTH)
    beacons = sum(1 for f in frames if f["frameType"] == FC_BEACON)
    probe_resp = sum(1 for f in frames if f["frameType"] == FC_PROBE_RESP)
    probe_req = sum(1 for f in frames if f["frameType"] == FC_PROBE_REQ)
    assoc_req = sum(1 for f in frames if f["frameType"] == FC_ASSOC_REQ)
    disassoc = sum(1 for f in frames if f["frameType"] == FC_DISASSOC)
    eapol_m1 = sum(1 for f in frames if EAPOL_KEY_MSG_1 in f.get("info", ""))
    eapol_m2 = sum(1 for f in frames if EAPOL_KEY_MSG_2 in f.get("info", ""))
    eapol_m3 = sum(1 for f in frames if EAPOL_KEY_MSG_3 in f.get("info", ""))
    eapol_m4 = sum(1 for f in frames if EAPOL_KEY_MSG_4 in f.get("info", ""))

    print(f"  Deauth帧: {deauth}")
    print(f"  Auth帧: {auth}")
    print(f"  Beacon帧: {beacons}")
    print(f"  Probe Request: {probe_req}")
    print(f"  Probe Response: {probe_resp}")
    print(f"  Association Request: {assoc_req}")
    print(f"  Disassociation: {disassoc}")
    print(f"  EAPOL M1/M2/M3/M4: {eapol_m1}/{eapol_m2}/{eapol_m3}/{eapol_m4}")

    # AP discovery
    ap_macs = set()
    for f in frames:
        if f["frameType"] == FC_BEACON:
            bssid = f.get("bssid", "") or f.get("sa", "")
            if bssid:
                ap_macs.add(bssid)
    print(f"  检测到AP MAC: {ap_macs}")

    # Security info
    sec = reader.get_beacon_security_info()
    if sec:
        print(f"  RSN版本: {sec.get('rsn_version')}")
        print(f"  组播加密: {sec.get('group_cipher')}")
        print(f"  成对加密: {sec.get('pairwise_cipher')}")
        print(f"  使用TKIP: {sec.get('uses_tkip')}")
        print(f"  使用WEP: {sec.get('uses_wep')}")

    # Discover all unique SSIDs
    ssids = set()
    for f in frames:
        ssid = f.get("ssid", "")
        if ssid:
            ssids.add(ssid)
    print(f"  检测到SSID: {ssids}")

    # Client MACs (auth/assoc request sources minus AP MACs)
    client_macs = set()
    for f in frames:
        if f["frameType"] in (FC_AUTH, FC_ASSOC_REQ):
            sa = f.get("sa", "")
            if sa and sa not in ap_macs:
                client_macs.add(sa)
    print(f"  检测到客户端MAC: {client_macs}")

    # Setup detectors
    detectors = [
        DeauthDetector(),
        FloodDetector(),
        BruteForceDetector(),
        EvilTwinDetector(),
        IllegalAccessDetector(),
        WeakPasswordDetector(),
        KrackDetector(),
    ]
    for d in detectors:
        if hasattr(d, "set_ap_macs"):
            d.set_ap_macs(ap_macs)

    # Process frames in chunks (~2 sec worth each)
    chunk_size = 264
    all_alerts = {d.name: [] for d in detectors}
    for i in range(0, len(frames), chunk_size):
        chunk = frames[i:i + chunk_size]
        for d in detectors:
            alert = d.analyze(chunk)
            if alert:
                all_alerts[d.name].append(alert)

    print(f"\n检测结果:")
    print("-" * 80)
    total = 0
    for d in detectors:
        alerts = all_alerts[d.name]
        total += len(alerts)
        print(f"\n{d.name} ({d.severity}): {len(alerts)} 次告警")
        for a in alerts:
            print(f"  源MAC: {a['sourceMac']}")
            print(f"  目标MAC: {a['targetMac']}")
            print(f"  时间: {a['timestamp']}")
            print(f"  建议: {a['suggestion'][:100]}...")
            print()

    print("-" * 80)
    print(f"总计: {total} 次告警")

    # Verify expected detections based on known pcap content
    print(f"\n验证:")
    expected = {
        "Deauth攻击": deauth > 100,
        "Flood泛洪": probe_resp > 1000 or deauth > 1000,
        "暴力破解": auth > 5,
        "非法接入": len(client_macs) > 0,
    }
    for name, should_detect in expected.items():
        detected = len(all_alerts.get(name, [])) > 0
        status = "PASS" if detected == should_detect else "FAIL"
        print(f"  {status}: {name} (期望检测={should_detect}, 实际检测={detected})")

    return all_alerts


def main():
    parser = argparse.ArgumentParser(description="Test WiFiGuard detection module")
    parser.add_argument("--pcap", help="Path to pcap file", default=None)
    parser.add_argument("--all", action="store_true", help="Test all testcase pcaps")
    args = parser.parse_args()

    test_dir = os.path.join(os.path.dirname(__file__), "testcase")

    if args.pcap:
        analyze_pcap(args.pcap)
    elif args.all:
        for fn in sorted(os.listdir(test_dir)):
            if fn.endswith(".cap") or fn.endswith(".pcap"):
                analyze_pcap(os.path.join(test_dir, fn))
                print("\n" + "=" * 80 + "\n")
    else:
        # Default: test global-01
        default = os.path.join(test_dir, "global-01.cap")
        if os.path.exists(default):
            analyze_pcap(default)


if __name__ == "__main__":
    main()
