# # agents/pitch_agent.py
# from .base_agent import BaseAgent
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# import torch

# MODEL_NAME = "google/flan-t5-small"

# class PitchAgent(BaseAgent):
#     def __init__(self):
#         super().__init__("PitchAgent")
#         self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
#         self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#         self.model.to(self.device)

#     def _generate(self, prompt, max_new_tokens=128):
#         inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
#         out = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
#         decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
#         return decoded

#     def run(self, business, findings):
#         """
#         business: {"name":..., "address":...}
#         findings: aggregated dict, must include explicit 'issues' list or fields used to craft pitch.
#         """
#         name = business.get("name", "Business")
#         issues = []
#         if findings.get("site_health", {}).get("issues"):
#             issues += findings["site_health"]["issues"]
#         if findings.get("social", {}):
#             # check for inactivity
#             ig = findings["social"].get("instagram")
#             if ig and ig.get("last_post"):
#                 issues.append(f"Instagram last post: {ig['last_post']}")
#             fb = findings["social"].get("facebook")
#             if fb and fb.get("followers") and fb.get("followers") < 200:
#                 issues.append(f"Low Facebook followers: {fb['followers']}")
#         # craft prompt for LLM
#         prompt = (
#             f"Write a short professional outreach email (3-5 sentences) to {name}. "
#             f"Use the following verified observations: {issues}. "
#             "Offer a concise value proposition for improving web presence and social engagement. "
#             "Include a single-line call-to-action and an unsubscribe sentence. Tone: friendly, professional."
#         )
#         pitch = self._generate(prompt, max_new_tokens=120)
#         return {"pitch": pitch}

# agents/pitch_agent.py
from .base_agent import BaseAgent
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import traceback

MODEL_NAME = "google/flan-t5-small"
# Translator model for English -> Hindi (Helsinki)
TRANSLATOR_EN_HI = "Helsinki-NLP/opus-mt-en-hi"

class PitchAgent(BaseAgent):
    def __init__(self):
        super().__init__("PitchAgent")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        # translator lazy load
        self.trans_tokenizer = None
        self.trans_model = None
        self.trans_device = self.device

    def _generate(self, prompt, max_new_tokens=128):
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(self.device)
        out = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return decoded

    def _ensure_translator(self, en_to="hi"):
        """
        Lazy load translator for en->hi only (expandable later).
        """
        if self.trans_model is None:
            if en_to == "hi":
                self.trans_tokenizer = AutoTokenizer.from_pretrained(TRANSLATOR_EN_HI)
                self.trans_model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATOR_EN_HI).to(self.trans_device)

    def _translate_en_to_hi(self, text):
        try:
            self._ensure_translator("hi")
            inputs = self.trans_tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.trans_device)
            out = self.trans_model.generate(**inputs, max_new_tokens=256)
            decoded = self.trans_tokenizer.decode(out[0], skip_special_tokens=True)
            return decoded
        except Exception:
            self._log("Translation failed: " + traceback.format_exc())
            return text

    def run(self, business, findings, language="en"):
        """
        business: {"name":..., "address":...}
        findings: aggregated dict, must include explicit 'issues' list or fields used to craft pitch.
        language: 'en' or 'hi' for Hindi (others not implemented)
        """
        name = business.get("name", "Business")
        issues = []
        if findings.get("site_health", {}).get("issues"):
            issues += findings["site_health"]["issues"]
        if findings.get("social", {}):
            # check for inactivity
            ig = findings["social"].get("instagram")
            if isinstance(ig, dict) and ig.get("last_post"):
                issues.append(f"Instagram last post: {ig['last_post']}")
            fb = findings["social"].get("facebook")
            if isinstance(fb, dict) and fb.get("followers") and isinstance(fb.get("followers"), int) and fb.get("followers") < 200:
                issues.append(f"Low Facebook followers: {fb['followers']}")
        # craft prompt for LLM (English)
        prompt = (
            f"Write a short professional outreach email (3-5 sentences) to {name}. "
            f"Use the following verified observations: {issues}. "
            "Offer a concise value proposition for improving web presence and social engagement. "
            "Include a single-line call-to-action and an unsubscribe sentence. Tone: friendly, professional."
        )
        pitch_en = self._generate(prompt, max_new_tokens=120)
        pitch_final = pitch_en
        if language and language.lower() != "en":
            if language.lower() == "hi":
                self._log("Translating pitch to Hindi")
                pitch_final = self._translate_en_to_hi(pitch_en)
            else:
                self._log(f"Requested language '{language}' not supported, returning English.")
        return {"pitch": pitch_final, "lang": language}
