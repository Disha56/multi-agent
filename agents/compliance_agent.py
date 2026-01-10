# agents/compliance_agent.py
from .base_agent import BaseAgent
import re

class ComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__("ComplianceAgent")
        # naive spam keywords
        self.spam_keywords = ["make money fast", "guaranteed", "earn cash", "click here", "free trial"]

    def run(self, pitch_text):
        issues = []
        # check for spam keywords
        lower = pitch_text.lower()
        for kw in self.spam_keywords:
            if kw in lower:
                issues.append(f"Contains spam keyword: {kw}")
        # check unsubscribe presence
        if "unsubscribe" not in lower and "opt-out" not in lower:
            issues.append("Missing unsubscribe/opt-out sentence")
        # check length
        if len(pitch_text) > 1200:
            issues.append("Pitch too long")
        return {"ok": len(issues) == 0, "issues": issues}
