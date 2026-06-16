class BaseDetector:
    name = ""
    severity = "medium"
    suggestion = ""

    def analyze(self, frames):
        """Analyze a batch of frames, return alert dict or None."""
        raise NotImplementedError

    def reset(self):
        """Reset internal state."""
        pass
