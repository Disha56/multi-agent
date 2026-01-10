# agents/digital_presence_agent.py
from .base_agent import BaseAgent
from services.site_scraper import extract_social_links_from_site, compute_basic_site_health, fetch_url
from bs4 import BeautifulSoup
import re

class DigitalPresenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("DigitalPresenceAgent")

    def run(self, website_url):
        self._log(f"Analyzing website: {website_url}")
        result = {"website": website_url}
        try:
            health = compute_basic_site_health(website_url)
            result["health"] = health
            social = extract_social_links_from_site(website_url)
            result["social_links"] = social
            # Try to fetch meta description
            r = fetch_url(website_url)
            soup = BeautifulSoup(r.text, "html.parser")
            desc = ""
            if soup.find("meta", attrs={"name": "description"}):
                desc = soup.find("meta", attrs={"name": "description"})["content"]
            result["meta_description"] = desc
        except Exception as e:
            self._log(f"Error analyzing {website_url}: {e}")
            result["error"] = str(e)
        return result
