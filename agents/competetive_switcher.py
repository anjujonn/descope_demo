import re

class CompetitiveSwitcherDetector:
    BAD_SENTIMENT = re.compile(r"migrate|moving away|downtime|incident|outage|broken|bug|doesn't work|vendor lock-in", re.I)

    def detect(self, text: str) -> bool:
        return bool(self.BAD_SENTIMENT.search(text or ""))
