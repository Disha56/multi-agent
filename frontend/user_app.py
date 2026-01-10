# frontend/user_app.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import Orchestrator
from utils.db import SessionLocal, fetch_all_businesses, mark_contacted, init_db
import pandas as pd
import io
import urllib.parse
from utils.email_sender import send_via_smtp
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="AlphaNeuron — User UI", layout="wide")
st.title("AlphaNeuron — Lead Finder (User)")

# Sidebar controls
with st.sidebar:
    st.header("Search")
    business_type = st.text_input("Business type", "dental clinic")
    city = st.text_input("City", "Ahmedabad")
    radius_km = st.number_input("Radius (km)", min_value=1, max_value=50, value=5)
    limit = st.slider("Max leads", 1, 30, 8)
    language = st.selectbox("Pitch language", ["en", "hi"], index=0)
    st.markdown("---")
    st.write("SMTP (optional for direct sending)")
    SMTP_HOST = st.text_input("SMTP host", "")
    SMTP_PORT = st.number_input("SMTP port", value=587)
    SMTP_USER = st.text_input("SMTP user/email", "")
    SMTP_PASS = st.text_input("SMTP password", type="password", value="")
    st.markdown("Tip: Leave SMTP blank to use your mail client (mailto).")

# Buttons
col1, col2 = st.columns([1,2])
with col1:
    if st.button("Run search"):
        with st.spinner("Running agents (may take a minute)..."):
            orch = Orchestrator()
            leads = orch.run(business_type, city, limit=limit, radius_km=radius_km, language=language)
            st.session_state["leads"] = leads
        st.success("Search complete")

# Display leads
if st.session_state.get("leads"):
    leads = st.session_state["leads"]
    df = pd.DataFrame([{
        "Name": l["name"],
        "Address": l.get("address") or "",
        "Phone": l.get("phone") or "",
        "Email": l.get("email") or "",
        "Instagram": l.get("instagram") or "",
        "LinkedIn": l.get("linkedin") or "",
        "Score": l["meta"]["score"]["grade"],
        "Opportunity": l["meta"]["score"]["opportunity_score"]
    } for l in leads])
    st.dataframe(df, use_container_width=True)

    for idx, lead in enumerate(leads):
        st.markdown("---")
        st.header(f"{lead['name']}")
        st.write("**Address:**", lead.get("address") or "—")
        st.write("**Phone:**", lead.get("phone") or "—")
        st.write("**Email:**", lead.get("email") or "—")
        st.write("**Instagram:**", lead.get("instagram") or "—")
        st.write("**LinkedIn:**", lead.get("linkedin") or "—")
        st.write("**Score:**", lead["meta"]["score"]["grade"], "| Opportunity:", lead["meta"]["score"]["opportunity_score"])
        st.subheader("Pitch (AlphaNeuron)")
        st.code(lead["meta"].get("pitch", "—"))

        # mailto link
        subject = urllib.parse.quote(f"Grow your {business_type} with AlphaNeuron")
        body_plain = lead["meta"].get("pitch", "")
        if "unsubscribe" not in body_plain.lower() and "opt out" not in body_plain.lower():
            body_plain += "\n\nTo opt out, reply 'unsubscribe'."
        body = urllib.parse.quote(body_plain)
        to = lead.get("email") or ""
        mailto_link = f"mailto:{to}?subject={subject}&body={body}"

        c1, c2 = st.columns([1,1])
        with c1:
            if st.button(f"Open mail client ({idx})"):
                js = f"window.open('{mailto_link}')"
                st.components.v1.html(f"<script>{js}</script>")
        with c2:
            if st.button(f"Send via SMTP ({idx})"):
                if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
                    st.error("Please fill SMTP credentials in the sidebar.")
                else:
                    ok, err = send_via_smtp(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                                            to if to else SMTP_USER,
                                            urllib.parse.unquote(subject),
                                            urllib.parse.unquote(body))
                    if ok:
                        st.success("Email sent via SMTP.")
                        # mark contacted in DB (we saved earlier results to DB in orchestrator)
                        session = SessionLocal()
                        # find matching DB row by name+address (basic)
                        rows = session.query.__self__.bind.execute  # placeholder; we will use fetch_all to find id
                        # simpler: search fetch_all_businesses by name
                        rows = fetch_all_businesses(SessionLocal())
                        # find likely id
                        match = None
                        for r in rows:
                            if r["name"] == lead["name"] and (lead.get("address") or "").split(",")[0] in (r.get("address") or ""):
                                match = r
                                break
                        if match:
                            mark_contacted(SessionLocal(), match["id"], method="smtp", contact_email=to if to else SMTP_USER, note="Sent via User UI SMTP")
                    else:
                        st.error(f"Send failed: {err}")
