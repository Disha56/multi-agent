# tools/sample_run.py
"""
Debug runner — runs a short discovery -> enrichment -> lead creation flow
Usage:
    python tools/sample_run.py --type "dental clinic" --city "Ahmedabad" --limit 3
"""
import argparse
import os
from dotenv import load_dotenv
load_dotenv()

# ensure project root is in path if running from tools/
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import Orchestrator
from utils.db import SessionLocal, fetch_all_businesses

def main(btype, city, limit):
    print("Starting local debug run")
    orch = Orchestrator()
    results = orch.run(btype, city, limit=limit, radius_km=5, language="en")
    print(f"\n--- DISCOVERED {len(results)} LEADS (printed) ---\n")
    for i, lead in enumerate(results, 1):
        print(f"LEAD #{i}")
        print("Name:", lead.get("name"))
        print("Address:", lead.get("address"))
        print("Top-level contact fields:")
        print("  Email:", lead.get("email") or lead.get("meta", {}).get("email"))
        print("  Phone:", lead.get("phone") or lead.get("meta", {}).get("phone"))
        print("  Website:", lead.get("website") or lead.get("meta", {}).get("website"))
        print("  Instagram:", lead.get("instagram") or lead.get("meta", {}).get("instagram"))
        print("  LinkedIn:", lead.get("linkedin") or lead.get("meta", {}).get("linkedin"))
        print("Site health (meta.site_health):", lead.get("meta", {}).get("site_health"))
        print("Social signals (meta.social):", lead.get("meta", {}).get("social"))
        print("Competitor info (meta.competitor):", lead.get("meta", {}).get("competitor"))
        score = lead.get("meta", {}).get("score", {})
        print("Score:", score.get("grade"), "Opportunity:", score.get("opportunity_score"))
        print("Pitch (meta.pitch):\n", lead.get("meta", {}).get("pitch"))
        print("-" * 60)

    print("\nSaved leads in data/businesses.db. You can open with DB Browser for SQLite or use the Admin UI.")
    print("\nExample SQL fetch (python):")
    session = SessionLocal()
    rows = fetch_all_businesses(session)
    print("Total rows in DB:", len(rows))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    main(args.type, args.city, args.limit)
