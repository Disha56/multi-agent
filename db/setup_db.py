# # db/setup_db.py
# import sqlite3
# import os

# DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "businesses.db")
# os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# conn = sqlite3.connect(DB_PATH)
# cur = conn.cursor()

# # cur.execute("""
# # CREATE TABLE IF NOT EXISTS businesses (
# #     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #     name TEXT,
# #     address TEXT,
# #     lat REAL,
# #     lng REAL,
# #     phone TEXT,
# #     email TEXT,
# #     website TEXT,
# #     instagram TEXT,
# #     linkedin TEXT,
# #     city TEXT,
# #     type TEXT,
# #     source TEXT,
# #     last_updated TEXT
# # )
# # """)

# db/setup_db.py
import sqlite3
import os

def initialize_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/businesses.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lat REAL,
            lng REAL,
            address TEXT,
            phone TEXT,
            email TEXT,
            instagram TEXT,
            linkedin TEXT,
            website TEXT,
            city TEXT,
            type TEXT,
            source TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized at data/businesses.db")
