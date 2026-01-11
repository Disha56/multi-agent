# services/google_places.py
import os, requests
from dotenv import load_dotenv
# load_dotenv is still safe if present; utils.config also will attempt to load .env
try:
    from utils.config import get_api_key, where_key_came_from
except Exception:
    # fallback if module path differs (run from different cwd)
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from utils.config import get_api_key, where_key_came_from

API_KEY = get_api_key("GOOGLE_PLACES_API_KEY")
KEY_ORIGIN = where_key_came_from("GOOGLE_PLACES_API_KEY")
HEADERS = {"User-Agent": os.getenv("USER_AGENT", "ai-business-intel-bot/1.0")}

PLACES_TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def is_enabled():
    return bool(API_KEY)

def search_places_google(query, location=None, radius_km=5, limit=20):
    if not is_enabled():
        raise RuntimeError(f"Google Places API key not found. Searched: {KEY_ORIGIN}")
    params = {"query": query, "key": API_KEY, "language": "en"}
    if location:
        params["location"] = location
        params["radius"] = int(radius_km * 1000)
    r = requests.get(PLACES_TEXT_URL, params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    # just return results list (caller will handle)
    return data

def get_place_details(place_id, fields="name,formatted_phone_number,website,formatted_address"):
    if not is_enabled():
        raise RuntimeError(f"Google Places API key not found. Searched: {KEY_ORIGIN}")
    params = {"place_id": place_id, "key": API_KEY, "fields": fields}
    r = requests.get(PLACES_DETAILS_URL, params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("result", {}) or {}
