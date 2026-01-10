# main.py
import argparse
from agents.orchestrator import Orchestrator
from utils.db import SessionLocal, fetch_all_businesses
import csv
import os

def cli():
    parser = argparse.ArgumentParser(description="Local AI-Agent Business Finder")
    parser.add_argument("--type", type=str, required=True, help="Business type to search (e.g., 'dental clinic')")
    parser.add_argument("--city", type=str, required=True, help="City name (e.g., Ahmedabad)")
    parser.add_argument("--limit", type=int, default=8, help="Number of businesses to process")
    parser.add_argument("--export-csv", type=str, default="", help="If provided, path to CSV file to export results after run")
    parser.add_argument("--language", type=str, default="en", help="Language for generated pitch: 'en' or 'hi'")
    args = parser.parse_args()
    orch = Orchestrator()
    out = orch.run(args.type, args.city, limit=args.limit)
    print("Done. Results saved to local SQLite database (data/businesses.db).")
    for o in out:
        print(o["name"], "-", o["meta"]["score"]["grade"], "-> pitch length:", len(o["meta"].get("pitch","")))

    if args.export_csv:
        session = SessionLocal()
        rows = fetch_all_businesses(session)
        # flatten minimal set for CSV
        fieldnames = ["id", "name", "lat", "lng", "address", "grade", "opportunity_score", "pitch"]
        os.makedirs(os.path.dirname(args.export_csv) or ".", exist_ok=True)
        with open(args.export_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                meta = r.get("meta", {})
                score = meta.get("score", {})
                pitch = meta.get("pitch", "")
                writer.writerow({
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "lat": r.get("lat"),
                    "lng": r.get("lng"),
                    "address": r.get("address"),
                    "grade": score.get("grade"),
                    "opportunity_score": score.get("opportunity_score"),
                    "pitch": pitch
                })
        print(f"Exported CSV to {args.export_csv}")

if __name__ == "__main__":
    cli()
