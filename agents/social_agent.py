# agents/social_agent.py
from .base_agent import BaseAgent
from services.social_tools import get_facebook_metrics, get_instagram_profile_metrics, get_twitter_metrics
from urllib.parse import urlparse
import re
import time

class SocialAgent(BaseAgent):
    def __init__(self):
        super().__init__("SocialAgent")

    def _normalize_handle(self, url_or_name):
        try:
            u = url_or_name.strip()
            if not u:
                return None
            if u.startswith("http"):
                path = urlparse(u).path
                parts = [p for p in path.split("/") if p]
                if parts:
                    return parts[-1]
                return None
            return u
        except Exception:
            return None

    def run(self, social_links):
        """
        social_links dict e.g. {"facebook": ["https://facebook.com/yourpage"], "instagram": [...], "twitter": [...]}
        """
        out = {}
        if not social_links:
            return out
        if "facebook" in social_links and social_links["facebook"]:
            fb = social_links["facebook"][0]
            self._log(f"Fetching facebook {fb}")
            out["facebook"] = get_facebook_metrics(fb)
        if "instagram" in social_links and social_links["instagram"]:
            ig = social_links["instagram"][0]
            handle = self._normalize_handle(ig)
            self._log(f"Fetching instagram {handle}")
            out["instagram"] = get_instagram_profile_metrics(handle)
        if "twitter" in social_links and social_links["twitter"]:
            tw = social_links["twitter"][0]
            handle = self._normalize_handle(tw)
            self._log(f"Fetching twitter {handle}")
            out["twitter"] = get_twitter_metrics(handle)
        return out

    def _candidate_handles(self, name):
        """
        Yield a list of likely handle candidates derived from a business name.
        Variants: remove punctuation, spaces->'', spaces->'_', spaces->'.', append city tokens not included here.
        """
        s = name.lower()
        # remove non-word characters except spaces
        s = re.sub(r'[^\w\s]', '', s)
        parts = s.split()
        # basic candidates
        yields = set()
        # full concatenations
        yields.add("".join(parts))
        yields.add("_".join(parts))
        yields.add(".".join(parts))
        # first + last pattern
        if len(parts) >= 2:
            yields.add(parts[0] + parts[-1])
            yields.add(parts[0] + "_" + parts[-1])
        # each token alone (useful for short names)
        for p in parts:
            yields.add(p)
        # small variations: remove vowels (sometimes used)
        def remove_vowels(x):
            return re.sub(r'[aeiou]', '', x)
        yields.add(remove_vowels("".join(parts)))
        # limit length to plausible handle length
        candidates = [h for h in yields if 2 <= len(h) <= 30]
        return candidates

    def discover_by_name(self, business_name, try_instagram=True, try_facebook=True, try_twitter=True, max_candidates=12):
        """
        Attempt to find public social profiles by guessing handles from the business name.
        Returns a dict with any found profiles (same format as run()).
        """
        results = {}
        candidates = self._candidate_handles(business_name)[:max_candidates]
        self._log(f"Attempting {len(candidates)} guessed handles for '{business_name}'")
        for candidate in candidates:
            # instagram
            if try_instagram and "instagram" not in results:
                try:
                    self._log(f"Trying instagram handle: {candidate}")
                    ig = get_instagram_profile_metrics(candidate)
                    if isinstance(ig, dict) and "error" not in ig:
                        results["instagram"] = ig
                        self._log(f"Found instagram: {candidate}")
                except Exception as e:
                    # be polite and short delay to avoid rapid firing
                    time.sleep(0.3)
            # facebook
            if try_facebook and "facebook" not in results:
                try:
                    self._log(f"Trying facebook handle/url: {candidate}")
                    fb = get_facebook_metrics(candidate)
                    if isinstance(fb, dict) and "error" not in fb:
                        results["facebook"] = fb
                        self._log(f"Found facebook: {candidate}")
                except Exception as e:
                    time.sleep(0.3)
            # twitter
            if try_twitter and "twitter" not in results:
                try:
                    self._log(f"Trying twitter handle: {candidate}")
                    tw = get_twitter_metrics(candidate)
                    if isinstance(tw, dict) and "error" not in tw:
                        results["twitter"] = tw
                        self._log(f"Found twitter: {candidate}")
                except Exception as e:
                    time.sleep(0.3)
            # stop early if found some profiles
            if results:
                # keep attempting a bit to gather multiple profiles
                if len(results) >= 2:
                    break
        return results