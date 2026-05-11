from detection.base import BaseDetector


class FloodDetector(BaseDetector):
    name = "Flood泛洪"
    severity = "medium"

    def analyze(self, devices):
        return None
