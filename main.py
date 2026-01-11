# # main_fetch.py
# import argparse
# from agents.discovery_agent import DiscoveryAgent
# from utils.db import init_db, SessionLocal, upsert_business
# import time

# def cli():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--type", required=True, help="Business type, e.g., 'dental clinic'")
#     parser.add_argument("--city", required=True, help="City name, e.g., 'Ahmedabad'")
#     parser.add_argument("--limit", type=int, default=10)
#     args = parser.parse_args()

#     init_db()
#     session = SessionLocal()
#     disc = DiscoveryAgent()
#     items = disc.run(args.type, args.city, limit=args.limit)
#     printed = 0
#     for it in items:
#         lead = {
#             "name": it.get("name"),
#             "address": it.get("address"),
#             "lat": it.get("lat"),
#             "lng": it.get("lng"),
#             "phone": it.get("phone"),
#             "email": it.get("email"),
#             "website": it.get("website"),
#             "instagram": it.get("instagram"),
#             "linkedin": it.get("linkedin"),
#             "meta": {}
#         }
#         obj, created = upsert_business(session, lead)
#         printed += 1
#         print(f"[Saved {'NEW' if created else 'UPDATED'}] {obj.id} | {obj.name} | {lead.get('phone') or ''} | {lead.get('instagram') or lead.get('linkedin') or ''}")
#     print(f"Done. {printed} items processed.")

# if __name__ == "__main__":
#     cli()



# main.py
import argparse
from agents.discovery_agent import DiscoveryAgent
from db.crud import upsert_business
from db.setup_db import initialize_db

def run_and_save(business_type, city, limit=10, radius_km=5):
    initialize_db()
    disc = DiscoveryAgent()
    items = disc.run(business_type, city, limit=limit, radius_km=radius_km)
    if not items:
        print("Done. 0 items processed.")
        return
    processed = 0
    for it in items:
        lead = {
            "name": it.get("name"),
            "address": it.get("address"),
            "lat": it.get("lat"),
            "lng": it.get("lng"),
            "phone": it.get("phone"),
            "email": it.get("email"),
            "website": it.get("website"),
            "instagram": it.get("instagram"),
            "linkedin": it.get("linkedin"),
            "city": city,
            "type": business_type,
            "source": it.get("source")
        }
        bid, created = upsert_business(lead)
        print(f"[Saved {'NEW' if created else 'UPDATED'}] {bid} | {lead.get('name')} | {lead.get('phone') or ''} | {lead.get('instagram') or lead.get('linkedin') or ''}")
        processed += 1
    print(f"Done. {processed} items processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--radius_km", type=int, default=5)
    args = parser.parse_args()
    run_and_save(args.type, args.city, limit=args.limit, radius_km=args.radius_km)
