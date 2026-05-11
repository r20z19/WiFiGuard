import re

MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


def is_valid_mac(mac):
    return bool(MAC_RE.match(mac))


def normalize_mac(mac):
    return mac.upper().replace("-", ":")
