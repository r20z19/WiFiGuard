import random
import time

from utils.time_utils import now_str

VIRTUAL_DEVICES = [
    {"mac": "AA:BB:CC:DD:EE:01", "ip": "192.168.1.100", "ssid": "WiFiGuard-Network", "signal": -45, "status": "正常", "is_ap": False},
    {"mac": "AA:BB:CC:DD:EE:02", "ip": "192.168.1.101", "ssid": "WiFiGuard-Network", "signal": -62, "status": "正常", "is_ap": False},
    {"mac": "AA:BB:CC:DD:EE:03", "ip": "192.168.1.1",   "ssid": "WiFiGuard-Network", "signal": -30, "status": "正常", "is_ap": True},
    {"mac": "11:22:33:44:55:01", "ip": "192.168.1.105", "ssid": "WiFiGuard-Network", "signal": -50, "status": "正常", "is_ap": False},
    {"mac": "11:22:33:44:55:02", "ip": "192.168.1.106", "ssid": "WiFiGuard-Network", "signal": -55, "status": "正常", "is_ap": False},
    {"mac": "BB:CC:DD:EE:FF:01", "ip": "192.168.1.110", "ssid": "WiFiGuard-Network", "signal": -72, "status": "正常", "is_ap": False},
    {"mac": "BB:CC:DD:EE:FF:02", "ip": "192.168.1.111", "ssid": "WiFiGuard-Network", "signal": -68, "status": "正常", "is_ap": False},
    {"mac": "CC:DD:EE:FF:AA:01", "ip": "192.168.1.120", "ssid": "WiFiGuard-Network", "signal": -80, "status": "可疑", "is_ap": False},
]

EVIL_TWIN_MACS = ["FF:EE:DD:CC:BB:01", "FF:EE:DD:CC:BB:02"]
DEAUTH_ATTACKER_MACS = ["AA:BB:CC:DD:EE:01", "66:77:88:99:AA:01"]
FLOOD_ATTACKER_MACS = ["BB:CC:DD:EE:FF:01", "BB:CC:DD:EE:FF:02"]
BRUTE_FORCE_MACS = ["11:22:33:44:55:01"]
ILLEGAL_MACS = ["66:77:88:99:AA:01", "DD:EE:FF:AA:BB:01"]

COMMON_WEAK_PASSWORDS = ["12345678", "88888888", "password", "11111111", "00000000", "adminadmin", "qwertyui"]
WEAK_ENCRYPTIONS = ["WEP", "WPA", "WPA2-TKIP"]


class SimulatorDataGenerator:

    def __init__(self):
        self._devices = [dict(d) for d in VIRTUAL_DEVICES]
        self._tick_count = 0
        self._deauth_counter = {}
        self._brute_force_counter = {}
        self._flood_counter = {}
        self._evil_twin_active = False
        self._evil_twin_phase = 0
        self._illegal_inserted = {}
        self._krack_checked = True
        self._krack_fired = False
        self._weak_password_checked = True
        self._weak_password_fired = False

    def tick(self):
        self._tick_count += 1
        now = now_str()

        for d in self._devices:
            d["signal"] = max(-95, min(-20, d["signal"] + random.randint(-3, 3)))
            d["lastSeen"] = now
            d["firstSeen"] = d.get("firstSeen", now)
            d["status"] = "正常" if d["signal"] > -75 else "可疑"

        self._check_evil_twin()
        self._check_deauth()
        self._check_flood()
        self._check_brute_force()
        self._check_illegal()
        self._check_weak_password()
        self._check_krack()

        return self._devices

    def get_attacks(self):
        attacks = []

        et = self._get_evil_twin_attack()
        if et:
            attacks.append(et)

        da = self._get_deauth_attack()
        if da:
            attacks.append(da)

        fl = self._get_flood_attack()
        if fl:
            attacks.append(fl)

        bf = self._get_brute_force_attack()
        if bf:
            attacks.append(bf)

        il = self._get_illegal_attack()
        if il:
            attacks.append(il)

        wp = self._get_weak_password_alert()
        if wp:
            attacks.append(wp)

        kr = self._get_krack_alert()
        if kr:
            attacks.append(kr)

        return attacks

    def _check_evil_twin(self):
        if self._tick_count == 15 and not self._evil_twin_active:
            self._evil_twin_active = True
            self._evil_twin_phase = self._tick_count

    def _check_deauth(self):
        if self._tick_count in (10, 25, 40):
            mac = random.choice(DEAUTH_ATTACKER_MACS)
            self._deauth_counter[mac] = self._deauth_counter.get(mac, 0) + 15

    def _check_flood(self):
        if self._tick_count in (18, 35):
            mac = random.choice(FLOOD_ATTACKER_MACS)
            self._flood_counter[mac] = self._flood_counter.get(mac, 0) + 5000

    def _check_brute_force(self):
        if self._tick_count == 20:
            mac = random.choice(BRUTE_FORCE_MACS)
            self._brute_force_counter[mac] = self._brute_force_counter.get(mac, 0) + 10

    def _check_illegal(self):
        if self._tick_count == 30:
            mac = ILLEGAL_MACS[0]
            self._illegal_inserted[mac] = now_str()
            self._devices.append({
                "mac": mac, "ip": "192.168.1.200",
                "ssid": "WiFiGuard-Network", "signal": -58,
                "status": "可疑", "is_ap": False,
                "firstSeen": now_str(), "lastSeen": now_str(),
            })

    def _check_weak_password(self):
        pass

    def _check_krack(self):
        pass

    def _get_evil_twin_attack(self):
        if self._evil_twin_active and self._tick_count == self._evil_twin_phase:
            return {
                "type": "钓鱼AP",
                "severity": "critical",
                "sourceMac": EVIL_TWIN_MACS[0],
                "targetMac": "Unknown",
                "timestamp": now_str(),
                "suggestion": "发现疑似钓鱼AP（Evil Twin），SSID与合法AP相似。请确认周围是否存在同名WiFi，建议立即断开当前连接并验证AP的BSSID是否为合法设备。使用802.11w PMF可提供额外保护。",
            }
        return None

    def _get_deauth_attack(self):
        for mac, count in list(self._deauth_counter.items()):
            if count > 0:
                self._deauth_counter[mac] = 0
                return {
                    "type": "Deauth攻击",
                    "severity": "high",
                    "sourceMac": mac,
                    "targetMac": "AA:BB:CC:DD:EE:02",
                    "timestamp": now_str(),
                    "suggestion": "检测到Deauth泛洪攻击，短时间内大量去认证帧被发送。建议启用802.11w PMF保护（Protected Management Frames），并检查AP是否配置了最大去认证速率限制。同时排查周边是否有可疑设备正在运行mdk4/aireplay-ng等攻击工具。",
                }
        return None

    def _get_flood_attack(self):
        for mac, count in list(self._flood_counter.items()):
            if count > 0:
                self._flood_counter[mac] = 0
                return {
                    "type": "Flood泛洪",
                    "severity": "medium",
                    "sourceMac": mac,
                    "targetMac": "AA:BB:CC:DD:EE:03",
                    "timestamp": now_str(),
                    "suggestion": "检测到无线泛洪攻击，网络中存在异常高频率的数据包传输。建议启用AP的速率限制功能，检查异常高流量设备的合法性，必要时使用WIPS（无线入侵防御系统）进行自动阻断。",
                }
        return None

    def _get_brute_force_attack(self):
        for mac, count in list(self._brute_force_counter.items()):
            if count > 0:
                self._brute_force_counter[mac] = 0
                return {
                    "type": "暴力破解",
                    "severity": "medium",
                    "sourceMac": mac,
                    "targetMac": "AA:BB:CC:DD:EE:03",
                    "timestamp": now_str(),
                    "suggestion": "检测到WiFi暴力破解尝试，短时间内出现大量认证失败记录。建议启用WPA3-SAE（Simultaneous Authentication of Equals），或确保WPA2-PSK使用强密码，并配置AP的认证失败速率限制和锁定策略。",
                }
        return None

    def _get_illegal_attack(self):
        for mac, ts in list(self._illegal_inserted.items()):
            if self._tick_count >= 30 and self._tick_count <= 33 and self._illegal_inserted.get(mac):
                if self._tick_count == 30:
                    return {
                        "type": "非法接入",
                        "severity": "high",
                        "sourceMac": mac,
                        "targetMac": "Unknown",
                        "timestamp": ts,
                        "suggestion": "检测到未知设备接入网络，该设备不在白名单中。请确认该设备是否为合法设备。如非预期设备，建议立即将其加入黑名单，检查路由器DHCP租约记录，并考虑更换WiFi密码以防止未授权访问。",
                    }
        return None

    def _get_weak_password_alert(self):
        if self._weak_password_checked and not self._weak_password_fired:
            self._weak_password_fired = True
            return {
                "type": "弱口令",
                "severity": "low",
                "sourceMac": "N/A",
                "targetMac": "AA:BB:CC:DD:EE:03",
                "timestamp": now_str(),
                "suggestion": "当前WiFi密码强度较弱，建议使用包含大小写字母、数字和特殊字符的至少12位密码。避免使用常见密码如'12345678'、'password'等。弱密码容易被字典攻击和暴力破解工具（如aircrack-ng、hashcat）在短时间内破解。",
            }
        return None

    def _get_krack_alert(self):
        if self._krack_checked and not self._krack_fired:
            self._krack_fired = True
            return {
                "type": "KRACK风险",
                "severity": "critical",
                "sourceMac": "N/A",
                "targetMac": "AA:BB:CC:DD:EE:03",
                "timestamp": now_str(),
                "suggestion": "检测到网络使用不安全的加密协议（WPA2-TKIP），存在KRACK（Key Reinstallation Attack）漏洞风险。建议立即升级AP固件至最新版本，并将加密方式切换为WPA2-AES（CCMP）或WPA3。同时确保所有客户端设备已安装最新的安全补丁。",
            }
        return None
