class BaseDetector:
    name = ""
    severity = "medium"
    suggestion = ""

    def analyze(self, devices):
        raise NotImplementedError
