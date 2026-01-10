# agents/competitor_agent.py
from .base_agent import BaseAgent
from services.osm_service import search_places_osm
import statistics

class CompetitorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CompetitorAgent")

    def run(self, business_name, lat, lng, radius_km=2, limit=10):
        self._log(f"Looking for competitors near {lat},{lng}")
        # We do a local search around same city via a naive search: use same business type search by name tokens
        tokens = business_name.split()
        query = tokens[0]  # naive
        results = search_places_osm(query, city=None, limit=limit)
        # For simplicity, compute competitor count and placeholder metrics
        comp_count = len(results)
        self._log(f"Found {comp_count} competitors (approx)")
        return {"competitor_count": comp_count, "sample_competitors": results[:5]}
