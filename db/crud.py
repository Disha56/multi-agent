# db/crud.py
from datetime import datetime
from db.helpers import get_connection

def now_iso():
    return datetime.utcnow().isoformat()

def _normalize_text(s):
    if s is None:
        return None
    return str(s).strip()

def find_existing(conn, name, address):
    """
    Return existing row id if a likely duplicate exists (match name exactly and address substring).
    """
    name = _normalize_text(name) or ""
    address = _normalize_text(address) or ""
    cur = conn.cursor()
    cur.execute("SELECT id, name, address FROM businesses WHERE name = ?", (name,))
    rows = cur.fetchall()
    for r in rows:
        rid, rname, raddr = r
        if raddr and address:
            if address.split(",")[0].strip().lower() in raddr.lower():
                return rid
    if rows:
        return rows[0][0]
    return None

def upsert_business(lead: dict):
    """
    Insert or update a business lead.
    lead keys: name,address,lat,lng,phone,email,website,instagram,linkedin,city,type,source
    Returns (id, created_bool)
    """
    conn = get_connection()
    try:
        existing_id = find_existing(conn, lead.get("name"), lead.get("address"))
        cur = conn.cursor()
        now = now_iso()
        if existing_id:
            fields = {
                "name": lead.get("name"),
                "address": lead.get("address"),
                "lat": lead.get("lat"),
                "lng": lead.get("lng"),
                "phone": lead.get("phone"),
                "email": lead.get("email"),
                "website": lead.get("website"),
                "instagram": lead.get("instagram"),
                "linkedin": lead.get("linkedin"),
                "city": lead.get("city"),
                "type": lead.get("type"),
                "source": lead.get("source"),
                "last_updated": now
            }
            set_parts = []
            params = []
            for k, v in fields.items():
                if v is not None:
                    set_parts.append(f"{k} = ?")
                    params.append(v)
            params.append(existing_id)
            if set_parts:
                sql = "UPDATE businesses SET " + ", ".join(set_parts) + " WHERE id = ?"
                cur.execute(sql, tuple(params))
                conn.commit()
            return existing_id, False
        else:
            sql = """
            INSERT INTO businesses
            (name,address,lat,lng,phone,email,website,instagram,linkedin,city,type,source,last_updated)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            params = (
                lead.get("name"),
                lead.get("address"),
                lead.get("lat"),
                lead.get("lng"),
                lead.get("phone"),
                lead.get("email"),
                lead.get("website"),
                lead.get("instagram"),
                lead.get("linkedin"),
                lead.get("city"),
                lead.get("type"),
                lead.get("source"),
                now
            )
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid, True
    finally:
        conn.close()

def fetch_all(filters: dict = None):
    conn = get_connection()
    cur = conn.cursor()
    sql = "SELECT * FROM businesses"
    where = []
    params = []
    if filters:
        if "name_contains" in filters:
            where.append("name LIKE ?")
            params.append(f"%{filters['name_contains']}%")
        if "city_contains" in filters:
            where.append("city LIKE ?")
            params.append(f"%{filters['city_contains']}%")
        if "type_contains" in filters:
            where.append("type LIKE ?")
            params.append(f"%{filters['type_contains']}%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY last_updated DESC"
    cur.execute(sql, tuple(params))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows

def fetch_by_id(bid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM businesses WHERE id = ?", (bid,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return None
    cols = [c[0] for c in cur.description]
    obj = dict(zip(cols, r))
    conn.close()
    return obj
