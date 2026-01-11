# services/web_search.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai-business-intel-bot/1.0)"}
DDG_HTML = "https://html.duckduckgo.com/html/"

def duckduckgo_search_urls(query, max_results=6):
    try:
        resp = requests.post(DDG_HTML, data={"q": query}, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        out = []
        # search result anchors
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href:
                out.append(href)
            if len(out) >= max_results:
                break
        # fallback anchors
        if not out:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href and href.startswith("http"):
                    out.append(href)
                if len(out) >= max_results:
                    break
        return out
    except Exception:
        return []
