from detection.base import BaseDetector


class BruteForceDetector(BaseDetector):
    name = "暴力破解"
    severity = "medium"

    def analyze(self, devices):
        return None
