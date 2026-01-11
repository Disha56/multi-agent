# agents/discovery_agent.py
import time, traceback, requests
from services.google_places import is_enabled as gp_enabled, search_places_google, get_place_details
# from services.geoapify import is_enabled as ga_enabled, search_places_geoapify
from services.web_search import duckduckgo_search_urls
from services.site_scraper import extract_social_links, extract_emails_and_phones

class DiscoveryAgent:
    def __init__(self):
        self.name = "DiscoveryAgent"

    def _log(self, *args):
        print(f"[DiscoveryAgent]", *args)

    def geocode_city(self, city):
        """Return (lat,lon) using Nominatim or None"""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            resp = requests.get(url, params={"q": city, "format": "json", "limit": 1},
                                headers={"User-Agent": "ai-business-intel-bot/1.0"}, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            self._log("geocode_city error:", e)
        return None

    def run(self, business_type, city, limit=10, radius_km=5):
        self._log(f"Searching for '{business_type}' in {city} limit={limit}")

        results = []
        seen = set()

        def add(item, source):
            key = f"{(item.get('name') or '').strip().lower()}|{item.get('lat')}|{item.get('lng')}"
            if key in seen:
                return
            seen.add(key)
            results.append({**item, "source": source})

        # Try geocode city to bias searches
        loc = self.geocode_city(city)
        if loc:
            self._log(f"Geocoded city {city} -> {loc[0]},{loc[1]}")
            location_param = f"{loc[0]},{loc[1]}"
        else:
            location_param = None
            self._log("City geocode failed; proceeding without location bias")



        # 1) Google: pass location if available
        if gp_enabled():
            try:
                q = f"{business_type} in {city}"
                self._log("Google enabled; querying with location:", location_param)
                g = search_places_google(q, location=location_param, radius_km=radius_km, limit=limit)
                for r in g:
                    if not isinstance(r, dict):
                        continue
                    details = {}
                    if r.get("place_id"):
                        try:
                            details = get_place_details(r.get("place_id"))
                        except Exception:
                            details = {}
                    item = {
                        "name": r.get("name"),
                        "lat": r.get("lat"),
                        "lng": r.get("lng"),
                        "address": r.get("address"),
                        "phone": details.get("formatted_phone_number"),
                        "website": details.get("website"),
                        "raw": {**r, "details": details}
                    }
                    add(item, "google")
                if len(results) >= limit:
                    self._log("Google filled required results")
                    return results[:limit]
            except Exception:
                self._log("Google error:", traceback.format_exc())
        time.sleep(0.3)

        # # 2) Geoapify fallback
        # if ga_enabled() and len(results) < limit:
        #     try:
        #         q = f"{business_type} {city}"
        #         self._log("Geoapify enabled; querying")
        #         # ga = search_places_geoapify(q, limit=(limit - len(results)))
        #         ga = search_places_geoapify(business_type, loc[0], loc[1], radius_km*1000, limit=(limit - len(results)))
        #         for r in ga:
        #             item = {
        #                 "name": r.get("name"),
        #                 "lat": r.get("lat"),
        #                 "lng": r.get("lng"),
        #                 "address": r.get("address"),
        #                 "phone": r.get("phone"),
        #                 "website": r.get("website"),
        #                 "raw": r.get("raw")
        #             }
        #             add(item, "geoapify")
        #         if len(results) >= limit:
        #             return results[:limit]
        #     except Exception:
        #         self._log("Geoapify error:", traceback.format_exc())
        # time.sleep(0.3)

        # 3) DuckDuckGo / website fallback and enrichment
        if len(results) < limit:
            if not results:
                urls = duckduckgo_search_urls(f"{business_type} {city} website", max_results=limit)
                for u in urls[:limit]:
                    add({"name": u.split("//")[-1].split("/")[0], "lat": None, "lng": None, "address": None, "phone": None, "website": u, "raw": {}}, "ddg")
            else:
                for item in results:
                    if not item.get("website"):
                        q = f"{item.get('name')} {city} website"
                        urls = duckduckgo_search_urls(q, max_results=3)
                        if urls:
                            item["website"] = urls[0]


        # enrich from website
        for item in results:
            if item.get("website"):
                self._log(f"Crawling website for socials: {item['website']}")
                try:
                    socials = extract_social_links(item["website"])
                    emails, phones = extract_emails_and_phones(item["website"])
                    
                    if socials.get("instagram"):
                        item["instagram"] = socials["instagram"][0]
                    else:
                        # Try DuckDuckGo fallback for Instagram
                        q = f"{item.get('name')} {city} Instagram site:instagram.com"
                        urls = duckduckgo_search_urls(q, max_results=1)
                        if urls:
                            item["instagram"] = urls[0]
                        elif emails:
                            item["email"] = emails[0]

                    if socials.get("linkedin"):
                        item["linkedin"] = socials["linkedin"][0]
                    if not item.get("phone") and phones:
                        item["phone"] = phones[0]
                    if not item.get("email") and emails and not item.get("instagram"):
                        item["email"] = emails[0]

                except Exception as e:
                    self._log("Error enriching website:", e)


        return results[:limit]
