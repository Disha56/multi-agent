# import sqlite3
# from db.helpers import get_connection
# conn = get_connection()


# DB_PATH = "data/businesses.db"

# def get_connection():
#     return sqlite3.connect(DB_PATH)


# db/helpers.py
import sqlite3
import os

# Ensure DB directory is deterministic (project root /data/businesses.db)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) if os.path.dirname(__file__) else "."
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "businesses.db")

os.makedirs(DB_DIR, exist_ok=True)

def get_connection():
    """
    Return a sqlite3.Connection to the shared DB.
    Use check_same_thread=False so multiple components (Streamlit + CLI) can open connections
    from the same process for demo purposes.
    """
    return sqlite3.connect(DB_PATH, check_same_thread=False)
