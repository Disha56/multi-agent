# # frontend/admin_app.py
# import streamlit as st
# import sys, os, time
# from db.helpers import get_connection
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from utils.db import SessionLocal, init_db, fetch_all
# import pandas as pd
# from dotenv import load_dotenv
# load_dotenv()

# st.set_page_config(page_title="Admin - Business Leads", layout="wide")
# st.title("Admin — Business Leads (Google+Geoapify)")

# init_db()
# session = SessionLocal()

# col1, col2 = st.columns([1,3])
# with col1:
#     st.header("Controls")
#     if st.button("Refresh list"):
#         # simple client reload
#         st.experimental_set_query_params(_refresh=int(time.time()))
#         st.components.v1.html("<script>window.location.reload();</script>")
#         st.stop()
#     q_type = st.text_input("Filter by type substring (name)", "")
#     q_city = st.text_input("Filter by city substring (address)", "")

# with col2:
#     st.markdown("This Admin UI displays leads saved in `data/businesses.db`. Use `main_fetch.py` to discover and save leads.")

# rows = fetch_all(session)
# # simple filters
# if q_type:
#     rows = [r for r in rows if q_type.lower() in (r["name"] or "").lower()]
# if q_city:
#     rows = [r for r in rows if r.get("address") and q_city.lower() in r["address"].lower()]

# if not rows:
#     st.info("No leads in DB. Run `python main_fetch.py --type 'dental clinic' --city 'Ahmedabad' --limit 6` from project root.")
# else:
#     df = pd.DataFrame([{
#         "id": r["id"],
#         "name": r["name"],
#         "address": r.get("address"),
#         "phone": r["meta"].get("phone",""),
#         "email": r["meta"].get("email",""),
#         "website": r["meta"].get("website",""),
#         "instagram": r["meta"].get("instagram",""),
#         "linkedin": r["meta"].get("linkedin",""),
#         "source": r.get("source","")
#     } for r in rows])
#     st.dataframe(df, use_container_width=True)

#     # per-row expand
#     for r in rows:
#         with st.expander(f"{r['name']} (ID {r['id']})", expanded=False):
#             st.write("Address:", r.get("address"))
#             st.write("Phone:", r["meta"].get("phone"))
#             st.write("Email:", r["meta"].get("email"))
#             st.write("Website:", r["meta"].get("website"))
#             st.write("Instagram:", r["meta"].get("instagram"))
#             st.write("LinkedIn:", r["meta"].get("linkedin"))
#             st.write("Source:", r.get("source"))

# frontend/admin_app.py

# import streamlit as st
# import pandas as pd
# import sqlite3

# st.set_page_config(page_title="Admin Panel", layout="wide")

# st.title("📊 Admin Dashboard - Business Leads")

# # Connect to DB
# conn = sqlite3.connect("data/businesses.db")
# df = pd.read_sql_query("SELECT * FROM businesses ORDER BY last_updated DESC", conn)

# if df.empty:
#     st.warning("No leads found.")
# else:
#     for _, row in df.iterrows():
#         st.subheader(f"{row['name']}")
#         st.markdown(f"**City:** {row['city']}")
#         st.markdown(f"**Type:** {row['type']}")
#         st.markdown(f"**Phone:** {row.get('phone', 'N/A')}")
#         st.markdown(f"**Email:** {row.get('email', 'N/A')}")
#         st.markdown(f"**Website:** {row.get('website', 'N/A')}")
#         st.markdown(f"**Instagram:** {row.get('instagram', 'N/A')}")
#         st.markdown(f"**LinkedIn:** {row.get('linkedin', 'N/A')}")
#         st.markdown("---")

# conn.close()


import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Admin Panel", layout="wide")

st.title("📊 Admin Dashboard - Business Leads")

DB_PATH = "data/businesses.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM businesses ORDER BY last_updated DESC", conn)
    conn.close()
    return df

# Manual refresh button
if st.button("🔁 Refresh Data"):
    st.cache_data.clear()

df = load_data()

if df.empty:
    st.warning("No leads found.")
    st.stop()

# Filter section
with st.expander("🔍 Filters"):
    selected_city = st.selectbox("City", ["All"] + sorted(df["city"].dropna().unique().tolist()))
    selected_type = st.selectbox("Business Type", ["All"] + sorted(df["type"].dropna().unique().tolist()))

    if selected_city != "All":
        df = df[df["city"] == selected_city]

    if selected_type != "All":
        df = df[df["type"] == selected_type]

# Display leads
for _, row in df.iterrows():
    st.subheader(row['name'])
    st.markdown(f"**Type**: {row['type']} | **City**: {row['city']}")
    st.markdown(f"**Phone**: {row.get('phone', 'N/A')} | **Email**: {row.get('email', 'N/A')}")
    st.markdown(f"**Website**: {row.get('website', 'N/A')}")
    st.markdown(f"**Instagram**: {row.get('instagram', 'N/A')}")
    st.markdown(f"**LinkedIn**: {row.get('linkedin', 'N/A')}")
    
    # Pitch email (if email exists)
    if row.get("email"):
        subject = f"Grow your {row['type']} with AlphaNeuron"
        body = f"""
        Hi {row['name']},

        We noticed your presence online could benefit from stronger visibility.

        At AlphaNeuron, we help local businesses grow using digital strategies across Instagram, LinkedIn, and more.

        Let's connect and show you how we can help you reach more customers.

        Regards,
        Team AlphaNeuron
        """

        if st.button(f"✉️ Send Pitch to {row['email']}", key=row['id']):
            st.info(f"Use this email to contact:\n\nTo: {row['email']}\n\nSubject: {subject}\n\n{body.strip()}")

    st.markdown("---")
