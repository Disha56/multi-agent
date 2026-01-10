# agents/discovery_agent.py
from .base_agent import BaseAgent
from services.osm_service import search_places_osm
from services.google_places import is_enabled, search_places_google, get_place_details
from time import sleep

class DiscoveryAgent(BaseAgent):
    def __init__(self):
        super().__init__("DiscoveryAgent")

    def run(self, business_type, city, limit=20, radius_km=5):
        self._log(f"Searching for '{business_type}' in {city} (limit={limit})")
        found = []
        # First try Google Places if enabled (more likely to have phone/website)
        if is_enabled():
            # build location lat,lng from city via OSM quick query
            # For simplicity: text search uses "business_type in city"
            try:
                g = search_places_google(f"{business_type} in {city}", radius_km=radius_km, limit=limit)
                for r in g:
                    # fetch details for phone/website
                    details = {}
                    if r.get("place_id"):
                        details = get_place_details(r.get("place_id")) or {}
                    found.append({
                        "name": r.get("name"),
                        "lat": r.get("lat"),
                        "lng": r.get("lng"),
                        "address": r.get("address"),
                        "website": details.get("website"),
                        "phone": details.get("formatted_phone_number"),
                        "raw": {**r, "details": details}
                    })
                if found:
                    self._log(f"Google Places returned {len(found)} results")
            except Exception as e:
                self._log(f"Google Places error: {e}")
        # If insufficient results, use OSM
        if len(found) < limit:
            needed = limit - len(found)
            osm_items = search_places_osm(business_type, city=city, limit=needed)
            for r in osm_items:
                found.append({
                    "name": r.get("name"),
                    "lat": r.get("lat"),
                    "lng": r.get("lng"),
                    "address": r.get("address"),
                    "website": None,
                    "phone": None,
                    "raw": r
                })
            self._log(f"OSM added {len(osm_items)} results")
        # normalize trimming to 'limit'
        return found[:limit]
