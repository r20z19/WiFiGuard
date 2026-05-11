from detection.base import BaseDetector


class DeauthDetector(BaseDetector):
    name = "Deauth攻击"
    severity = "high"

    def analyze(self, devices):
        return None
