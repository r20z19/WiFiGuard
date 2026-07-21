"""Network activity log — records events for AI analysis."""

from collections import deque
import threading

# Thread-safe circular buffer of network events
_event_buffer = deque(maxlen=500)
_lock = threading.Lock()


def log_event(event_type, mac="", detail=""):
    """Add an event to the activity log."""
    from utils.time_utils import now_str
    with _lock:
        _event_buffer.append({
            "time": now_str(),
            "type": event_type,
            "mac": mac,
            "detail": detail,
        })

# Frame type map for human-readable output
FC_MAP = {
    0: "管理帧(Association)",
    1: "管理帧(Association Resp)",
    2: "管理帧(Reassociation)",
    3: "管理帧(Reassociation Resp)",
    4: "管理帧(Probe Request)",
    5: "管理帧(Probe Response)",
    8: "管理帧(Beacon)",
    10: "管理帧(Disassociation)",
    12: "管理帧(Deauthentication)",
    13: "管理帧(Action)",
    32: "数据帧(Data)",
    40: "数据帧(QoS Data)",
    44: "数据帧(QoS Null)",
}


def _describe_frame(f):
    """Convert a raw frame dict to a human-readable one-liner."""
    ft = f.get("frameType", "?")
    fc = f.get("fc", "")
    subtype = f.get("subtype", "")
    sa = f.get("sa", "")
    da = f.get("da", "")
    bssid = f.get("bssid", "")
    ssid = f.get("ssid", "")
    signal = f.get("signal")
    ip_info = f.get("ip", "")

    ft_desc = FC_MAP.get(ft, f"类型{ft}")

    parts = [ft_desc]
    if sa:
        parts.append(f"源={sa}")
    if da:
        parts.append(f"目标={da}")
    if bssid and bssid != sa:
        parts.append(f"BSSID={bssid}")
    if ssid:
        parts.append(f"SSID={ssid}")
    if signal is not None:
        parts.append(f"信号={signal}dBm")
    if ip_info:
        parts.append(f"IP={ip_info}")
    if subtype:
        parts.append(f"子类型={subtype}")

    return " | ".join(parts)


def log_device_event(mac, status, detail=""):
    """Log a device-related event."""
    log_event("device", mac, f"{status}: {detail}")


def log_attack_event(alert_type, source_mac, target_mac, severity):
    """Log an attack event."""
    log_event("attack", source_mac,
              f"类型={alert_type} 目标={target_mac} 等级={severity}")


def get_recent_events(limit=50):
    """Get the most recent events."""
    with _lock:
        return list(_event_buffer)[-limit:]


def get_events_by_mac(mac, limit=30):
    """Get recent events involving a specific MAC."""
    mac_lower = mac.lower().replace(":", "").replace("-", "")
    results = []
    with _lock:
        for e in reversed(_event_buffer):
            e_mac = (e.get("mac", "") or "").lower().replace(":", "").replace("-", "")
            detail = (e.get("detail", "") or "").lower()
            if mac_lower in e_mac or mac_lower in detail:
                results.append(e)
                if len(results) >= limit:
                    break
    return list(reversed(results))


def get_attack_context(mac):
    """Get network activity context for a specific MAC — for AI analysis."""
    events = get_events_by_mac(mac, 30)
    if not events:
        # Build synthetic context from available info
        return {"hasData": False, "message": f"设备 {mac} 无最近活动记录（模拟模式下不产生原始帧数据）"}

    attack_events = [e for e in events if e["type"] == "attack"]
    device_events = [e for e in events if e["type"] == "device"]

    return {
        "hasData": True,
        "totalEvents": len(events),
        "attackEvents": len(attack_events),
        "deviceEvents": len(device_events),
        "recentActivity": [
            f"[{e['time']}] {e['type']}: {e.get('detail', e.get('mac', ''))}"
            for e in events[-15:]
        ],
        "summary": (
            f"最近共{len(events)}个事件，其中攻击事件{len(attack_events)}个，"
            f"设备事件{len(device_events)}个"
        ),
    }


def get_frame_summary(mac=None, limit=20):
    """Return event summary, optionally filtered by MAC."""
    events = get_events_by_mac(mac, limit) if mac else get_recent_events(limit)
    return {
        "total": len(events),
        "events": [
            f"[{e['time']}] {e['type']}: {e.get('detail', e.get('mac', ''))}"
            for e in events
        ],
    }
