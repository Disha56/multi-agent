# services/site_scraper.py
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from dotenv import load_dotenv
load_dotenv()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai-business-intel-bot/1.0)"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{6,}\d)")

def fetch_html(url, timeout=8):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def extract_social_links(url):
    """Return dict {instagram: [urls], linkedin: [urls], facebook: [urls], website: url}"""
    html = fetch_html(url)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("/"):
            href = urljoin(url, href)
        if "instagram.com" in href:
            out.setdefault("instagram", []).append(href.split("?")[0])
        if "linkedin.com" in href:
            out.setdefault("linkedin", []).append(href.split("?")[0])
        if "facebook.com" in href:
            out.setdefault("facebook", []).append(href.split("?")[0])
    return out

def extract_emails_and_phones(url):
    html = fetch_html(url)
    emails = set()
    phones = set()
    if not html:
        return [], []
    for m in EMAIL_RE.findall(html):
        emails.add(m)
    for m in PHONE_RE.findall(html):
        cleaned = re.sub(r"[\s\-()]", "", m)
        if 6 <= len(cleaned) <= 15:
            phones.add(cleaned)
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            emails.add(href.split("mailto:")[1].split("?")[0])
        if href.startswith("tel:"):
            phones.add(re.sub(r"[\s\-()]", "", href.split("tel:")[1]))
    return list(emails), list(phones)
