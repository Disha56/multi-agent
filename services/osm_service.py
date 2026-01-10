# services/osm_service.py
import requests
from urllib.parse import urlencode
from urllib.parse import quote_plus
from utils.helpers import retry_on_exception

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {"User-Agent": "ai-business-intel-bot/1.0"}

def search_places_osm(query, city=None, limit=20):
    """
    Simple Nominatim search. Query e.g. "dental clinic, Ahmedabad"
    Returns list of {name, lat, lon, display_name}
    """
    q = query
    if city:
        q = f"{query}, {city}, India"
    params = {"q": q, "format": "json", "limit": limit}
    url = f"{NOMINATIM_URL}?{urlencode(params)}"
    resp = retry_on_exception(lambda: requests.get(url, headers=HEADERS, timeout=10), attempts=3)
    data = resp.json()
    out = []
    for item in data:
        out.append({
            "name": item.get("display_name").split(",")[0],
            "lat": float(item.get("lat")),
            "lng": float(item.get("lon")),
            "address": item.get("display_name"),
            "raw": item
        })
    return out
