from detection.base import BaseDetector


class IllegalAccessDetector(BaseDetector):
    name = "非法接入"
    severity = "high"

    def analyze(self, devices):
        return None
