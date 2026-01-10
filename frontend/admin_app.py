# frontend/admin_app.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.db import SessionLocal, fetch_all_businesses, fetch_business_by_id, delete_business, mark_contacted, add_manual_lead, update_business_meta
from utils.email_sender import send_via_smtp
import pandas as pd
import io
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="AlphaNeuron — Admin", layout="wide")
st.title("AlphaNeuron — Admin Dashboard")

session = SessionLocal()

# Sidebar filters and actions
with st.sidebar:
    st.header("Filters & Actions")
    filter_city = st.text_input("Filter by city (address contains)", "")
    filter_contacted = st.selectbox("Contacted status", options=["all", "contacted", "not_contacted"], index=0)
    name_search = st.text_input("Name contains", "")
    st.markdown("---")
    st.header("SMTP for admin sends")
    SMTP_HOST = st.text_input("SMTP host", "")
    SMTP_PORT = st.number_input("SMTP port", value=587)
    SMTP_USER = st.text_input("SMTP user/email", "")
    SMTP_PASS = st.text_input("SMTP password", type="password", value="")
    st.markdown("---")
    st.write("Add manual lead")
    m_name = st.text_input("Name (manual)", key="m_name")
    m_address = st.text_input("Address (manual)", key="m_address")
    m_email = st.text_input("Email (manual)", key="m_email")
    m_phone = st.text_input("Phone (manual)", key="m_phone")
    if st.button("Add manual lead"):
        if not m_name:
            st.error("Name required")
        else:
            meta = {"score": {"grade": "UNKNOWN", "opportunity_score": 0}, "contact_history": [], "contacted": False}
            lead = {"name": m_name, "address": m_address, "lat": None, "lng": None, "source": "manual", "meta": meta}
            added = add_manual_lead(session, lead)
            st.success(f"Added lead ID {added['id']}")

# Build filters
filters = {}
if filter_contacted == "contacted":
    filters["contacted"] = True
elif filter_contacted == "not_contacted":
    filters["contacted"] = False
if name_search:
    filters["name_contains"] = name_search
if filter_city:
    filters["city"] = filter_city

rows = fetch_all_businesses(session, filters=filters)
st.write(f"Found {len(rows)} leads (filtered)")

# Dataframe summary
df = pd.DataFrame([{
    "id": r["id"],
    "Name": r["name"],
    "Address": r.get("address") or "",
    "Contacted": r["meta"].get("contacted", False),
    "Last Contacted": r["meta"].get("last_contacted") or ""
} for r in rows])
st.dataframe(df, use_container_width=True)

# Export CSV
csv_buf = io.StringIO()
pd.DataFrame(rows).to_csv(csv_buf, index=False)
if st.button("Export CSV of filtered leads"):
    st.download_button("Download CSV", data=csv_buf.getvalue(), file_name="alpha_leads_export.csv", mime="text/csv")

# Per-lead management
st.markdown("---")
st.header("Lead management")
lead_id = st.number_input("Lead ID", min_value=1, value=1)
if st.button("Load lead"):
    lead = fetch_business_by_id(session, lead_id)
    if not lead:
        st.error("Lead not found")
    else:
        st.subheader(f"{lead['name']} (ID {lead['id']})")
        st.write("Address:", lead.get("address"))
        st.write("Meta:", lead.get("meta"))
        # Contact history
        st.write("Contact history:")
        for h in lead["meta"].get("contact_history", []):
            st.write(h)
        # Actions
        st.markdown("### Actions")
        # Compose a quick email using meta pitch if exists
        pitch = lead["meta"].get("pitch") or st.text_area("Custom pitch", value="", height=150)
        to = lead["meta"].get("email") or st.text_input("Recipient email", value=lead["meta"].get("email") or "")
        subj = st.text_input("Subject", value=f"Grow your business with AlphaNeuron")
        if st.button("Send this email (Admin SMTP)"):
            if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
                st.error("Please set SMTP in sidebar")
            else:
                ok, err = send_via_smtp(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, to if to else SMTP_USER, subj, pitch)
                if ok:
                    st.success("Sent; updating contact history")
                    mark_contacted(session, lead_id, method="admin_smtp", contact_email=to, note="Sent via admin UI")
                else:
                    st.error(f"Send failed: {err}")
        if st.button("Mark as contacted (manual)"):
            mark_contacted(session, lead_id, method="manual", contact_email=None, note="Marked manually by admin")
            st.success("Marked as contacted")
        if st.button("Delete lead"):
            if delete_business(session, lead_id):
                st.success("Deleted")
            else:
                st.error("Delete failed")

st.markdown("---")
st.write("Admin panel ready. Use filters above to find leads, add manual leads, and manage outreach.")
