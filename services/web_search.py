# services/web_search.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
from utils.helpers import retry_on_exception
HEADERS = {"User-Agent": "ai-business-intel-bot/1.0"}

DDG_HTML = "https://html.duckduckgo.com/html/"

def duckduckgo_search(query, max_results=8):
    """
    Minimal DDG HTML search: returns list of result URLs.
    """
    params = {"q": query}
    def _req():
        return requests.post(DDG_HTML, data=params, headers=HEADERS, timeout=10)
    resp = retry_on_exception(_req, attempts=2)
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for a in soup.select("a.result__a, a[href]"):
        href = a.get("href")
        if href:
            out.append(href)
        if len(out) >= max_results:
            break
    # filter and normalize
    return out

def find_profiles_by_search(business_name, city=None, max_results=10):
    """
    Search queries like 'business_name city instagram' and 'business_name city linkedin'
    Return a dict with possible 'instagram' and 'linkedin' urls (first matches).
    """
    found = {}
    q_inst = f"{business_name} {city or ''} instagram"
    q_link = f"{business_name} {city or ''} linkedin"
    # instagram
    for url in duckduckgo_search(q_inst, max_results=max_results):
        if "instagram.com" in url:
            found.setdefault("instagram", []).append(url)
    for url in duckduckgo_search(q_link, max_results=max_results):
        if "linkedin.com" in url:
            found.setdefault("linkedin", []).append(url)
    # website guess
    q_site = f"{business_name} {city or ''} website"
    for url in duckduckgo_search(q_site, max_results=4):
        # heuristics: prefer business domains (not result page)
        u = url.lower()
        if any(ext in u for ext in [".com", ".in", ".net", ".co.in"]):
            found.setdefault("website_candidates", []).append(url)
    return found
