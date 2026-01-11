# tools/gp_test.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.google_places import get_businesses
import json

res = get_businesses("dental clinic", "Ahmedabad", limit=3)
print("GP results count:", len(res))
print(json.dumps(res, indent=2))
