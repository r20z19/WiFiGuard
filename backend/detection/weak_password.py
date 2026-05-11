from detection.base import BaseDetector


class WeakPasswordDetector(BaseDetector):
    name = "弱口令"
    severity = "low"

    def analyze(self, devices):
        return None
