# services/site_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.helpers import retry_on_exception
import re

USER_AGENT = "ai-business-intel-bot/1.0"
HEADERS = {"User-Agent": USER_AGENT}

def fetch_url(url, timeout=10):
    return retry_on_exception(lambda: requests.get(url, headers=HEADERS, timeout=timeout), attempts=2)

def extract_social_links_from_site(url):
    try:
        r = fetch_url(url)
    except Exception:
        return {}
    soup = BeautifulSoup(r.text, "html.parser")
    out = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "facebook.com" in href and "profile.php" not in href:
            out.setdefault("facebook", set()).add(href.split("?")[0])
        if "instagram.com" in href and "p/" not in href:
            out.setdefault("instagram", set()).add(href.split("?")[0])
        if "twitter.com" in href or "x.com" in href:
            out.setdefault("twitter", set()).add(href.split("?")[0])
        if "youtube.com" in href or "youtu.be" in href:
            out.setdefault("youtube", set()).add(href.split("?")[0])
        if "linkedin.com" in href:
            out.setdefault("linkedin", set()).add(href.split("?")[0])
    return {k: list(v) for k, v in out.items()}

def compute_basic_site_health(url):
    try:
        r = fetch_url(url)
        status = r.status_code
        ok = 200 <= status < 400
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        has_contact = False
        for a in soup.find_all("a", href=True):
            if "contact" in a["href"].lower() or "book" in a["href"].lower() or "appointment" in a["href"].lower():
                has_contact = True
                break
        ssl = url.startswith("https")
        issues = []
        if not ok:
            issues.append(f"HTTP status {status}")
        if not title:
            issues.append("No title")
        if not has_contact:
            issues.append("No obvious contact/book CTA")
        if not ssl:
            issues.append("No HTTPS")
        score = max(0, 100 - 20 * len(issues))
        return {"reachable": ok, "status_code": status, "title": title, "has_contact": has_contact, "ssl": ssl, "issues": issues, "score": score}
    except Exception as e:
        return {"reachable": False, "status_code": None, "title": "", "has_contact": False, "ssl": False, "issues": [str(e)], "score": 0}

_email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_phone_regex = re.compile(r"(\+?\d{1,4}[\s-]?)?(\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4})")

def extract_emails_from_site(url):
    try:
        r = fetch_url(url)
    except Exception:
        return []
    text = r.text
    emails = set(re.findall(_email_regex, text))
    # also look for mailto:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            mail = href.split("mailto:")[1].split("?")[0]
            emails.add(mail)
    return list(emails)

def extract_phones_from_site(url):
    try:
        r = fetch_url(url)
    except Exception:
        return []
    text = r.text
    # Find probable phone numbers; filter junk
    candidates = set()
    for m in re.findall(_phone_regex, text):
        # m is tuple groups, join
        num = "".join(m)
        # normalize: remove spaces
        normal = re.sub(r"[\s\-\(\)]", "", num)
        # length heuristics
        if 6 <= len(normal) <= 15:
            candidates.add(normal)
    # also check visible 'tel:' links
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("tel:"):
            t = href.split("tel:")[1]
            candidates.add(re.sub(r"[\s\-\(\)]", "", t))
    return list(candidates)