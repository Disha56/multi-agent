# utils/db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) if os.path.dirname(__file__) else "."
DB_PATH = os.path.join(BASE_DIR, "data", "businesses.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False, "timeout": 30})
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, record):
    try:
        c = dbapi_connection.cursor()
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA synchronous=NORMAL;")
        c.execute("PRAGMA busy_timeout=30000;")
        c.close()
    except Exception:
        pass

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
    source = Column(String)
    meta = Column(JSON, default={})

def init_db():
    Base.metadata.create_all(bind=engine)

def find_existing(session, name, address):
    q = session.query(Business).filter(Business.name == name).all()
    for r in q:
        if r.address and address and address.split(",")[0].strip().lower() in r.address.lower():
            return r
    return q[0] if q else None

def upsert_business(session, lead):
    existing = find_existing(session, lead.get("name") or "", lead.get("address") or "")
    meta = lead.get("meta") or {}
    # flatten known fields into meta
    for k in ["email","phone","instagram","linkedin","website","score"]:
        if k not in meta:
            meta[k] = lead.get(k) or lead.get("meta", {}).get(k)
    if existing:
        existing.meta = {**(existing.meta or {}), **meta}
        if not existing.lat and lead.get("lat"):
            existing.lat = lead.get("lat")
        if not existing.lng and lead.get("lng"):
            existing.lng = lead.get("lng")
        if not existing.address and lead.get("address"):
            existing.address = lead.get("address")
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing, False
    else:
        b = Business(
            name = lead.get("name"),
            lat = lead.get("lat"),
            lng = lead.get("lng"),
            address = lead.get("address"),
            source = lead.get("source", "composite"),
            meta = meta
        )
        session.add(b)
        session.commit()
        session.refresh(b)
        return b, True

def fetch_all(session):
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
    return out
