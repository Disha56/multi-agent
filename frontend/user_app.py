# # # frontend/user_app.py
# # import streamlit as st
# # import sys, os
# # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# # from agents.orchestrator import Orchestrator
# # from utils.db import SessionLocal, upsert_business
# # import pandas as pd
# # import urllib.parse
# # from dotenv import load_dotenv
# # load_dotenv()

# # st.set_page_config(page_title="AlphaNeuron — User UI", layout="wide")
# # st.title("AlphaNeuron — Lead Finder (User)")

# # with st.sidebar:
# #     st.header("Search")
# #     business_type = st.text_input("Business type", "dental clinic")
# #     city = st.text_input("City", "Ahmedabad")
# #     radius_km = st.number_input("Radius (km)", min_value=1, max_value=50, value=5)
# #     limit = st.slider("Max leads", 1, 30, 8)
# #     language = st.selectbox("Pitch language", ["en", "hi"], index=0)
# #     st.markdown("---")
# #     st.write("Note: This user UI opens your local mail client for outreach (mailto). Admin handles SMTP sends.")

# # if "leads" not in st.session_state:
# #     st.session_state["leads"] = []

# # col1, col2 = st.columns([1,2])
# # with col1:
# #     if st.button("Run search"):
# #         with st.spinner("Running agents (may take a minute)..."):
# #             orch = Orchestrator()
# #             leads = orch.run(business_type, city, limit=limit, radius_km=radius_km, language=language)
# #             # persist leads to DB (upsert)
# #             session = SessionLocal()
# #             persisted = []
# #             for l in leads:
# #                 obj, created = upsert_business(session, l)
# #                 # fetch canonical output for UI display (merge meta + top-level)
# #                 out = {
# #                     "id": obj.id,
# #                     "name": obj.name,
# #                     "address": obj.address,
# #                     "lat": obj.lat,
# #                     "lng": obj.lng,
# #                     "meta": obj.meta or {}
# #                 }
# #                 persisted.append(out)
# #             st.session_state["leads"] = persisted
# #         st.success(f"Search complete — {len(st.session_state['leads'])} leads saved to DB")

# # if st.session_state.get("leads"):
# #     df = pd.DataFrame([{
# #         "id": l["id"],
# #         "Name": l["name"],
# #         "Address": l.get("address",""),
# #         "Score": l["meta"].get("score",{}).get("grade",""),
# #         "Opportunity": l["meta"].get("score",{}).get("opportunity_score",0)
# #     } for l in st.session_state["leads"]])
# #     st.dataframe(df, use_container_width=True)

# #     for idx, lead in enumerate(st.session_state["leads"]):
# #         st.markdown("---")
# #         st.header(f"{lead['name']}")
# #         st.write("Address:", lead.get("address") or "—")
# #         st.write("Score:", lead["meta"].get("score",{}).get("grade",""))
# #         st.write("Opportunity:", lead["meta"].get("score",{}).get("opportunity_score",0))
# #         st.subheader("Pitch (AlphaNeuron)")
# #         st.code(lead["meta"].get("pitch","—"))

# #         # mailto
# #         subject = urllib.parse.quote(f"Grow your {business_type} with AlphaNeuron")
# #         body_plain = lead["meta"].get("pitch","")
# #         if "unsubscribe" not in body_plain.lower():
# #             body_plain += "\n\nTo opt out, reply 'unsubscribe'."
# #         body = urllib.parse.quote(body_plain)
# #         to = lead["meta"].get("email") or ""
# #         mailto_link = f"mailto:{to}?subject={subject}&body={body}"

# #         if st.button(f"Open mail client for '{lead['name']}'", key=f"mailto_{lead['id']}"):
# #             js = f"window.open('{mailto_link}')"
# #             st.components.v1.html(f"<script>{js}</script>")


# # frontend/user_app.py
# import streamlit as st
# from agents.discovery_agent import DiscoveryAgent
# from db.setup_db import initialize_db
# from db.crud import upsert_business, fetch_all
# import pandas as pd

# st.set_page_config(page_title="AlphaNeuron — User UI", layout="wide")
# st.title("AlphaNeuron — Lead Finder (User)")

# initialize_db()

# with st.sidebar:
#     st.header("Search")
#     business_type = st.text_input("Business type", "dental clinic")
#     city = st.text_input("City", "Ahmedabad")
#     limit = st.number_input("Max results", min_value=1, max_value=50, value=6)
#     radius_km = st.number_input("Radius (km)", min_value=1, max_value=50, value=5)
#     st.markdown("---")
#     st.write("Run a search to discover and save leads into the shared DB.")

# col1, col2 = st.columns([1,3])
# with col1:
#     if st.button("Run search and save"):
#         with st.spinner("Running discovery (Google / Geoapify)..."):
#             agent = DiscoveryAgent()
#             results = agent.run(business_type, city, limit=limit, radius_km=radius_km)
#             saved = []
#             for r in results:
#                 lead = {
#                     "name": r.get("name"),
#                     "address": r.get("address"),
#                     "lat": r.get("lat"),
#                     "lng": r.get("lng"),
#                     "phone": r.get("phone"),
#                     "email": r.get("email"),
#                     "website": r.get("website"),
#                     "instagram": r.get("instagram"),
#                     "linkedin": r.get("linkedin"),
#                     "city": city,
#                     "type": business_type,
#                     "source": r.get("source")
#                 }
#                 bid, created = upsert_business(lead)
#                 saved.append((bid, created, lead))
#         st.success(f"Saved {len(saved)} leads to DB")

# with col2:
#     st.header("Recent leads (from DB)")
#     rows = fetch_all()
#     if rows:
#         df = pd.DataFrame([{
#             "id": r["id"],
#             "name": r["name"],
#             "address": r["address"],
#             "phone": r["phone"],
#             "instagram": r["instagram"],
#             "linkedin": r["linkedin"],
#             "city": r["city"],
#             "type": r["type"],
#             "last_updated": r["last_updated"]
#         } for r in rows])
#         st.dataframe(df, use_container_width=True)
#     else:
#         st.info("No leads yet. Run a search from the sidebar.")


# frontend/user_app.py

# import streamlit as st
# import pandas as pd
# import sqlite3

# st.set_page_config(page_title="User View", layout="wide")

# st.title("🔍 Business Search")

# city = st.text_input("Enter City", "Ahmedabad")
# business_type = st.text_input("Enter Business Type", "dental clinic")

# if st.button("Search"):
#     conn = sqlite3.connect("data/businesses.db")
#     query = """
#         SELECT * FROM businesses
#         WHERE city LIKE ? AND type LIKE ?
#         ORDER BY last_updated DESC
#     """
#     df = pd.read_sql_query(query, conn, params=(f"%{city}%", f"%{business_type}%"))
#     conn.close()

#     if df.empty:
#         st.warning("No results found.")
#     else:
#         for _, row in df.iterrows():
#             st.subheader(row['name'])
#             st.markdown(f"**Address:** {row['address']}")
#             st.markdown(f"**Phone:** {row.get('phone', 'N/A')}")
#             st.markdown(f"**Email:** {row.get('email', 'N/A')}")
#             st.markdown(f"**Instagram:** {row.get('instagram', 'N/A')}")
#             st.markdown(f"**LinkedIn:** {row.get('linkedin', 'N/A')}")
#             st.markdown("---")


import streamlit as st
import sqlite3
import os
import pandas as pd

st.set_page_config(page_title="Business Discovery", layout="wide")

st.title("🔎 Discover Local Businesses")

city = st.text_input("City", "Ahmedabad")
biz_type = st.text_input("Business Type", "dental clinic")
limit = st.slider("Result Limit", 1, 20, 6)

if st.button("Search & Fetch"):
    # Call discovery from main.py dynamically
    command = f'python main.py --type "{biz_type}" --city "{city}" --limit {limit}'
    st.info(f"Running discovery: `{command}`")
    os.system(command)
    st.success("Discovery completed. Showing updated results.")

    # Now show results
    conn = sqlite3.connect("data/businesses.db")
    query = "SELECT * FROM businesses WHERE city=? AND type=? ORDER BY last_updated DESC"
    df = pd.read_sql_query(query, conn, params=(city, biz_type))
    conn.close()

    if df.empty:
        st.warning("No businesses found.")
    else:
        for _, row in df.iterrows():
            st.subheader(row["name"])
            st.markdown(f"**Phone:** {row.get('phone', 'N/A')}")
            st.markdown(f"**Email:** {row.get('email', 'N/A')}")
            st.markdown(f"**Instagram:** {row.get('instagram', 'N/A')}")
            st.markdown(f"**LinkedIn:** {row.get('linkedin', 'N/A')}")
            st.markdown("---")
