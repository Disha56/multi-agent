# agents/growth_agent.py
from .base_agent import BaseAgent
import math
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load a small free model (flan-t5-small). This will download on first run.
MODEL_NAME = "google/flan-t5-small"

class GrowthAgent(BaseAgent):
    def __init__(self):
        super().__init__("GrowthAgent")
        self._log("Loading local LLM model (may take a moment)...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        # use no_cuda by default if torch.device not cuda
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _llm_explain(self, prompt, max_new_tokens=128):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return decoded

    def run(self, aggregated_signal):
        """
        aggregated_signal: dict with keys: site_health (score 0-100), social (dict), competitor (competitor_count), reviews (optional)
        """
        site_score = aggregated_signal.get("site_health", {}).get("score", 0)
        social = aggregated_signal.get("social", {})
        # compute social score heuristics
        social_score = 0
        # facebook followers if available
        if social.get("facebook") and isinstance(social["facebook"], dict) and social["facebook"].get("followers"):
            social_score += min(50, social["facebook"].get("followers", 0) / 10)  # scaling
        if social.get("instagram") and isinstance(social["instagram"], dict) and social["instagram"].get("followers"):
            social_score += min(30, social["instagram"].get("followers", 0) / 20)
        # twitter engagement
        if social.get("twitter") and isinstance(social["twitter"], dict):
            social_score += min(20, social["twitter"].get("avg_likes", 0) / 2)
        competitor_count = aggregated_signal.get("competitor", {}).get("competitor_count", 0)
        # opportunity score: low competitors + low social/site => high opportunity
        opportunity = max(0, 100 - (site_score * 0.6 + social_score * 0.7) + max(0, 10 - competitor_count) * 5)
        # normalize
        opportunity = max(0, min(100, opportunity))
        grade = "LOW"
        if opportunity > 70:
            grade = "HIGH"
        elif opportunity > 40:
            grade = "MEDIUM"
        # LLM explanation
        prompt = (
            "You are an explainable scoring assistant. Given the site score, social signals, and competitor info, "
            f"explain concisely why opportunity={opportunity:.1f} and grade={grade}. "
            f"Site score: {site_score}. Social sample: {social}. Competitors: {competitor_count}.\n\nExplanation:"
        )
        explanation = self._llm_explain(prompt, max_new_tokens=128)
        return {"opportunity_score": opportunity, "grade": grade, "explanation": explanation}
