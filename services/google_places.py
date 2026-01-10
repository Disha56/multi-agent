# services/google_places.py
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
PLACES_TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
HEADERS = {"User-Agent": os.getenv("USER_AGENT", "ai-business-intel-bot/1.0")}

def is_enabled():
    return bool(API_KEY)

def search_places_google(query, location=None, radius_km=5, limit=20):
    """
    Query google places text search. If no API key configured, returns [].
    location: "lat,lng" or None
    """
    if not is_enabled():
        return []
    params = {"query": query, "key": API_KEY, "language": "en", "type": "establishment", "pagetoken": ""}
    if location:
        params["location"] = location
        params["radius"] = int(radius_km * 1000)
    params["maxresults"] = limit
    url = f"{PLACES_TEXT_URL}?{urlencode({k:v for k,v in params.items() if v})}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    data = resp.json()
    out = []
    for r in data.get("results", [])[:limit]:
        out.append({
            "name": r.get("name"),
            "lat": r.get("geometry", {}).get("location", {}).get("lat"),
            "lng": r.get("geometry", {}).get("location", {}).get("lng"),
            "address": r.get("formatted_address"),
            "place_id": r.get("place_id"),
            "raw": r
        })
    return out

def get_place_details(place_id):
    if not is_enabled() or not place_id:
        return {}
    params = {"place_id": place_id, "key": API_KEY, "fields": "name,formatted_phone_number,website,formatted_address,adr_address"}
    resp = requests.get(PLACES_DETAILS_URL, params=params, timeout=10)
    data = resp.json().get("result", {})
    return data
