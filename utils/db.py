# utils/db.py
import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "businesses.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lng = Column(Float)
    address = Column(Text)
    source = Column(String)  # e.g. 'osm' or 'composite'
    meta = Column(JSON, default={})      # arbitrary json: social links, metrics, scores

def init_db():
    Base.metadata.create_all(bind=engine)

def save_business(session, biz_dict):
    """
    Insert a new business row. biz_dict must include at least: name, lat, lng, address, source, meta.
    Returns the Business object.
    """
    # Ensure meta has contact_history structure
    meta = biz_dict.get("meta") or {}
    if "contact_history" not in meta:
        meta["contact_history"] = []
    if "contacted" not in meta:
        meta["contacted"] = False
    if "last_contacted" not in meta:
        meta["last_contacted"] = None
    b = Business(
        name=biz_dict.get("name"),
        lat=biz_dict.get("lat"),
        lng=biz_dict.get("lng"),
        address=biz_dict.get("address"),
        source=biz_dict.get("source", "unknown"),
        meta=meta,
    )
    session.add(b)
    session.commit()
    session.refresh(b)
    return b

def fetch_all_businesses(session, filters=None):
    """
    Return list of dict rows. filters is a dict: e.g. {"city": "...", "contacted": False}
    For now we ignore city filtering (store address contains city)
    """
    rows = session.query(Business).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "name": r.name,
            "lat": r.lat,
            "lng": r.lng,
            "address": r.address,
            "source": r.source,
            "meta": r.meta or {}
        })
    if not filters:
        return out
    # basic filtering: by contacted status or name substring
    res = out
    if "contacted" in filters:
        res = [r for r in res if bool(r["meta"].get("contacted", False)) == bool(filters["contacted"])]
    if "name_contains" in filters:
        key = filters["name_contains"].lower()
        res = [r for r in res if key in (r["name"] or "").lower()]
    if "city" in filters:
        key = filters["city"].lower()
        res = [r for r in res if r["address"] and key in r["address"].lower()]
    return res

def fetch_business_by_id(session, biz_id):
    r = session.query(Business).filter(Business.id == int(biz_id)).first()
    if not r:
        return None
    return {
        "id": r.id,
        "name": r.name,
        "lat": r.lat,
        "lng": r.lng,
        "address": r.address,
        "source": r.source,
        "meta": r.meta or {}
    }

def update_business_meta(session, biz_id, meta_update: dict):
    """
    Merge meta_update into existing meta and commit.
    """
    r = session.query(Business).filter(Business.id == int(biz_id)).first()
    if not r:
        return None
    meta = r.meta or {}
    # shallow merge
    meta.update(meta_update)
    r.meta = meta
    session.add(r)
    session.commit()
    session.refresh(r)
    return {
        "id": r.id,
        "name": r.name,
        "meta": r.meta
    }

def mark_contacted(session, biz_id, method="manual", contact_email=None, note=None):
    """
    Append a contact entry to meta.contact_history, set meta.contacted True, last_contacted timestamp.
    method: 'mailto', 'smtp', 'manual'
    """
    r = session.query(Business).filter(Business.id == int(biz_id)).first()
    if not r:
        return None
    meta = r.meta or {}
    history = meta.get("contact_history", [])
    entry = {
        "ts": now_iso(),
        "method": method,
        "email": contact_email,
        "note": note
    }
    history.append(entry)
    meta["contact_history"] = history
    meta["contacted"] = True
    meta["last_contacted"] = entry["ts"]
    r.meta = meta
    session.add(r)
    session.commit()
    session.refresh(r)
    return {"id": r.id, "meta": r.meta}

def delete_business(session, biz_id):
    r = session.query(Business).filter(Business.id == int(biz_id)).first()
    if not r:
        return False
    session.delete(r)
    session.commit()
    return True

def add_manual_lead(session, lead_dict):
    """
    lead_dict should include name, address, lat, lng (optional), source (optional), meta (optional)
    """
    meta = lead_dict.get("meta") or {}
    if "contact_history" not in meta:
        meta["contact_history"] = []
    if "contacted" not in meta:
        meta["contacted"] = False
    if "last_contacted" not in meta:
        meta["last_contacted"] = None
    b = Business(
        name=lead_dict.get("name"),
        address=lead_dict.get("address"),
        lat=lead_dict.get("lat"),
        lng=lead_dict.get("lng"),
        source=lead_dict.get("source", "manual"),
        meta=meta
    )
    session.add(b)
    session.commit()
    session.refresh(b)
    return {
        "id": b.id,
        "name": b.name,
        "address": b.address,
        "meta": b.meta
    }
