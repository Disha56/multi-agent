# agents/orchestrator.py
from .base_agent import BaseAgent
from .discovery_agent import DiscoveryAgent
from .digital_presence_agent import DigitalPresenceAgent
from .social_agent import SocialAgent
from .competitor_agent import CompetitorAgent
from .growth_agent import GrowthAgent
from .pitch_agent import PitchAgent
from .compliance_agent import ComplianceAgent
from utils.db import init_db, SessionLocal, save_business
from services.web_search import find_profiles_by_search
from services.site_scraper import extract_emails_from_site, extract_phones_from_site
import os

class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__("Orchestrator")
        self.discovery = DiscoveryAgent()
        self.digital = DigitalPresenceAgent()
        self.social = SocialAgent()
        self.competitor = CompetitorAgent()
        self.growth = GrowthAgent()
        self.pitch = PitchAgent()
        self.compliance = ComplianceAgent()
        init_db()
        self.db = SessionLocal()

    def run(self, business_type, city, limit=10, radius_km=5, language="en"):
        results = []
        found = self.discovery.run(business_type, city, limit=limit, radius_km=radius_km)
        for b in found:
            name = b.get("name") or "Unknown"
            self._log(f"Processing: {name}")
            website = b.get("website")
            phone = b.get("phone")
            email_candidates = []
            linkedin = None
            instagram = None

            digital_info = {}
            if website:
                digital_info = self.digital.run(website)
                emails = extract_emails_from_site(website)
                phones = extract_phones_from_site(website)
                if emails:
                    email_candidates.extend(emails)
                if phones and not phone:
                    phone = phones[0]
                social_links = digital_info.get("social_links", {})
                if social_links.get("linkedin"):
                    linkedin = social_links["linkedin"][0]
                if social_links.get("instagram"):
                    instagram = social_links["instagram"][0]
            else:
                self._log("No website; using web search to find profiles")
                found_profiles = find_profiles_by_search(name, city=city, max_results=6)
                if found_profiles.get("website_candidates"):
                    website_guess = found_profiles["website_candidates"][0]
                    self._log(f"Found website candidate: {website_guess}")
                    try:
                        digital_info = self.digital.run(website_guess)
                        emails = extract_emails_from_site(website_guess)
                        phones = extract_phones_from_site(website_guess)
                        if emails:
                            email_candidates.extend(emails)
                        if phones and not phone:
                            phone = phones[0]
                    except Exception:
                        pass
                if found_profiles.get("linkedin"):
                    linkedin = found_profiles["linkedin"][0]
                if found_profiles.get("instagram"):
                    instagram = found_profiles["instagram"][0]

            # social discovery / guess
            social_info = {}
            if instagram or linkedin:
                social_links = {}
                if instagram:
                    social_links["instagram"] = [instagram]
                if linkedin:
                    social_links["linkedin"] = [linkedin]
                social_info = self.social.run(social_links)
            else:
                social_info = self.social.discover_by_name(name)

            # attempt to extract email from social about fields if none found
            if not email_candidates:
                fb = social_info.get("facebook")
                if isinstance(fb, dict):
                    about = fb.get("about","")
                    import re
                    m = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", str(about))
                    if m:
                        email_candidates.extend(m)
            final_email = email_candidates[0] if email_candidates else None

            competitor_info = self.competitor.run(name, b.get("lat"), b.get("lng"))
            aggregated = {"site_health": digital_info.get("health", {}), "social": social_info, "competitor": competitor_info}
            score = self.growth.run(aggregated)
            findings = {"site_health": aggregated["site_health"], "social": aggregated["social"], "competitor": competitor_info, "score": score}

            # build lead record (keep contact fields at top-level and inside meta)
            lead = {
                "name": name,
                "address": b.get("address"),
                "lat": b.get("lat"),
                "lng": b.get("lng"),
                "phone": phone,
                "email": final_email,
                "instagram": None,
                "linkedin": None,
                "website": website or (digital_info.get("website") if digital_info else None),
                "meta": findings
            }
            # map social_info to fields
            if social_info.get("instagram"):
                ig = social_info.get("instagram")
                if isinstance(ig, dict) and ig.get("username"):
                    lead["instagram"] = ig.get("username")
                else:
                    # may be URL or dict
                    if isinstance(ig, str):
                        lead["instagram"] = ig
                    elif isinstance(ig, dict) and ig.get("username"):
                        lead["instagram"] = ig.get("username")
            if social_info.get("linkedin"):
                ln = social_info.get("linkedin")
                if isinstance(ln, list):
                    lead["linkedin"] = ln[0]
                elif isinstance(ln, str):
                    lead["linkedin"] = ln

            # generate pitch when needed
            pitch_text = ""
            if score["grade"] in ["HIGH", "MEDIUM"]:
                pitch = self.pitch.run(lead, findings, language=language)
                pitch_text = pitch.get("pitch", "")
                comp = self.compliance.run(pitch_text)
                if not comp.get("ok"):
                    self._log(f"Compliance issues: {comp.get('issues')}")
                    if "Missing unsubscribe/opt-out sentence" in comp.get("issues", []):
                        pitch_text += "\n\nTo opt out, reply 'unsubscribe'."

            # store contact fields inside meta for admin convenience
            meta_to_save = lead["meta"]
            meta_to_save.update({
                "email": lead.get("email"),
                "phone": lead.get("phone"),
                "instagram": lead.get("instagram"),
                "linkedin": lead.get("linkedin"),
                "website": lead.get("website"),
                "pitch": pitch_text
            })
            # attach pitch into meta and mark defaults for contact history
            lead["meta"] = meta_to_save

            # persist to DB (save_business ensures meta.contact_history etc)
            save_business(self.db, {
                "name": lead["name"],
                "lat": lead["lat"],
                "lng": lead["lng"],
                "address": lead["address"],
                "source": "composite",
                "meta": lead["meta"],
                # keep top-level contact fields too (save_business copies top-level into meta)
                "email": lead.get("email"),
                "phone": lead.get("phone"),
                "instagram": lead.get("instagram"),
                "linkedin": lead.get("linkedin"),
                "website": lead.get("website")
            })
            results.append(lead)
        return results
