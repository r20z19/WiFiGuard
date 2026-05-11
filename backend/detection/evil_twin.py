from detection.base import BaseDetector


class EvilTwinDetector(BaseDetector):
    name = "钓鱼AP"
    severity = "critical"

    def analyze(self, devices):
        return None
