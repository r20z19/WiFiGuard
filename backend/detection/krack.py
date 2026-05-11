from detection.base import BaseDetector


class KrackDetector(BaseDetector):
    name = "KRACK风险"
    severity = "critical"

    def analyze(self, devices):
        return None
