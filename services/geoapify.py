# services/geoapify.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEOAPIFY_API_KEY", "").strip()
HEADERS = {"User-Agent": os.getenv("USER_AGENT", "ai-business-intel-bot/1.0")}
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

def is_enabled():
    return bool(API_KEY)

def search_places_geoapify(business_type, lat, lon, radius_m=5000, limit=20, lang="en"):
    if not is_enabled():
        return []

    # Optional: map common business types to Geoapify categories
    category_map = {
        "dental clinic": "healthcare.dentist",
        "clinic": "healthcare.clinic",
        "hospital": "healthcare.hospital",
        "pharmacy": "healthcare.pharmacy",
        "optical": "healthcare.optician",
        "salon": "beauty.salon"
    }
    category = category_map.get(business_type.lower(), "commercial.services")

    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},{radius_m}",
        "limit": min(limit, 50),
        "apiKey": API_KEY,
        "lang": lang
    }

    r = requests.get(GEOAPIFY_PLACES_URL, params=params, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()

    out = []
    for f in data.get("features", [])[:limit]:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None])
        out.append({
            "name": props.get("name"),
            "lat": coords[1],
            "lng": coords[0],
            "address": props.get("formatted"),
            "phone": props.get("phone"),
            "website": props.get("website"),
            "raw": f
        })
    return out
