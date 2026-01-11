# frontend/streamlit_app.py
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import Orchestrator
from utils.db import SessionLocal, fetch_all_businesses
import pandas as pd
import io
import urllib.parse
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
from db.helpers import get_connection

st.set_page_config(layout="wide")
st.title("AlphaNeuron — Local Business Lead Finder (India)")

with st.sidebar:
    st.header("Search parameters")
    business_type = st.text_input("Business type", "dental clinic")
    city = st.text_input("City", "Ahmedabad")
    radius_km = st.number_input("Search radius (km)", min_value=1, max_value=50, value=5)
    limit = st.slider("Max leads", 1, 30, 8)
    language = st.selectbox("Pitch language", ["en", "hi"], index=0)
    st.markdown("---")
    st.write("Optional SMTP (for direct send)")
    SMTP_HOST = st.text_input("SMTP host (leave blank for mailto)", value="")
    SMTP_PORT = st.number_input("SMTP port", value=587)
    SMTP_USER = st.text_input("SMTP user/email", value="")
    SMTP_PASS = st.text_input("SMTP password", type="password", value="")
    st.markdown("**Note:** Using SMTP will send emails directly from this machine. Use responsibly.")

col1, col2 = st.columns([1,2])
with col1:
    if st.button("Run search"):
        st.session_state["running"] = True
        with st.spinner("Running agents (this may take a minute)..."):
            orch = Orchestrator()
            leads = orch.run(business_type, city, limit=limit, radius_km=radius_km, language=language)
            st.session_state["leads"] = leads
        st.success("Done")
with col2:
    if st.session_state.get("leads"):
        st.write(f"Found {len(st.session_state['leads'])} leads")

if st.session_state.get("leads"):
    leads = st.session_state["leads"]
    # display table summary
    df = pd.DataFrame([{
        "Name": l["name"],
        "Address": l["address"],
        "Phone": l.get("phone") or "",
        "Email": l.get("email") or "",
        "Instagram": l.get("instagram") or "",
        "LinkedIn": l.get("linkedin") or "",
        "Score": l["meta"]["score"]["grade"],
        "Opportunity": l["meta"]["score"]["opportunity_score"]
    } for l in leads])
    st.dataframe(df, use_container_width=True)

    for idx, l in enumerate(leads):
        st.markdown("---")
        st.header(f"{l['name']}")
        c1, c2, c3 = st.columns([2,2,1])
        with c1:
            st.markdown(f"**Address:** {l.get('address')}")
            st.markdown(f"**Phone:** {l.get('phone') or '—'}")
            st.markdown(f"**Email:** {l.get('email') or '—'}")
        with c2:
            st.markdown(f"**Instagram:** {l.get('instagram') or '—'}")
            st.markdown(f"**LinkedIn:** {l.get('linkedin') or '—'}")
            st.markdown(f"**Website:** {l.get('website') or '—'}")
        with c3:
            st.markdown(f"**Score:** {l['meta']['score']['grade']}")
            st.markdown(f"**Opportunity:** {l['meta']['score']['opportunity_score']:.1f}")

        st.subheader("Generated Pitch (AlphaNeuron)")
        st.code(l["meta"].get("pitch", "No pitch generated"))
        # Compose mailto
        subject = urllib.parse.quote(f"Grow your {business_type} with AlphaNeuron")
        body_plain = l["meta"].get("pitch", "")
        # Append our signature opt-out line if not present
        if "opt out" not in body_plain.lower() and "unsubscribe" not in body_plain.lower():
            body_plain += "\n\nTo opt out, reply 'unsubscribe'."
        body = urllib.parse.quote(body_plain)
        to = l.get("email") or ""
        mailto_link = f"mailto:{to}?subject={subject}&body={body}"

        csend1, csend2 = st.columns([1,1])
        with csend1:
            if st.button(f"Open mail client ({idx})"):
                # open mailto link in new tab
                js = f"window.open('{mailto_link}')"
                st.components.v1.html(f"<script>{js}</script>")
        with csend2:
            if st.button(f"Send via SMTP ({idx})"):
                if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
                    st.error("SMTP credentials missing in sidebar.")
                else:
                    try:
                        msg = EmailMessage()
                        msg["Subject"] = urllib.parse.unquote(subject)
                        msg["From"] = SMTP_USER
                        msg["To"] = to if to else SMTP_USER
                        msg.set_content(urllib.parse.unquote(body))
                        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                            s.starttls()
                            s.login(SMTP_USER, SMTP_PASS)
                            s.send_message(msg)
                        st.success("Sent via SMTP (check Sent folder).")
                    except Exception as e:
                        st.error(f"SMTP send failed: {e}")