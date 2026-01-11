# tools/debug_api_check.py
import os, json, requests, sys
from pathlib import Path

# ensure project root on sys.path for utils imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.config import get_api_key, get_dotenv_path, where_key_came_from

def masked(s):
    if not s:
        return None
    s = s.strip()
    if len(s) <= 10:
        return s[0:2] + "..." + s[-2:]
    return s[0:4] + "..." + s[-4:]

def print_header(t):
    print("\n" + "="*10 + " " + t + " " + "="*10)

def test_google(query="dental clinic in Ahmedabad"):
    print_header("Google Places Test")
    key = get_api_key("GOOGLE_PLACES_API_KEY")
    origin = where_key_came_from("GOOGLE_PLACES_API_KEY")
    print("Key (masked):", masked(key), "| origin:", origin)
    if not key:
        print("-> Google key not found. Please ensure .env is in project root or environment variable is set.")
        return
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": key, "language": "en"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": os.getenv("USER_AGENT","ai-business-intel-bot/1.0")}, timeout=10)
        print("HTTP", r.status_code)
        j = r.json()
        print("status:", j.get("status"))
        print("results_count:", len(j.get("results", [])))
        if j.get("results"):
            print("first_result.name:", j["results"][0].get("name"))
    except Exception as e:
        print("Google request error:", e)

def test_geoapify(query="dental clinic Ahmedabad"):
    print_header("Geoapify Test")
    key = get_api_key("GEOAPIFY_API_KEY")
    origin = where_key_came_from("GEOAPIFY_API_KEY")
    print("Key (masked):", masked(key), "| origin:", origin)
    if not key:
        print("-> Geoapify key not found.")
        return
    url = "https://api.geoapify.com/v2/places"
    params = {"text": query, "limit": 3, "format": "json", "apiKey": key}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": os.getenv("USER_AGENT","ai-business-intel-bot/1.0")}, timeout=10)
        print("HTTP", r.status_code)
        j = r.json()
        print("features:", len(j.get("features", [])))
        if j.get("features"):
            props = j["features"][0].get("properties", {})
            print("first_result.name:", props.get("name"))
    except Exception as e:
        print("Geoapify request error:", e)

def geocode_city(city="Ahmedabad"):
    print_header("Nominatim Geocode")
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": os.getenv("USER_AGENT","ai-business-intel-bot/1.0")}, timeout=10)
        print("HTTP", r.status_code)
        j = r.json()
        print("results:", len(j))
        if j:
            print("lat, lon:", j[0].get("lat"), j[0].get("lon"))
    except Exception as e:
        print("Nominatim error:", e)

if __name__ == "__main__":
    print("Env .env path attempted:", get_dotenv_path())
    test_google()
    test_geoapify()
    geocode_city()
