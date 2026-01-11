# tools/psql_test_insert.py
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
DB_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:1234567890@localhost:5432/business_db")

def test_insert():
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor()
    try:
        print("Connected OK")
        cur.execute("INSERT INTO businesses (name, address) VALUES (%s,%s) RETURNING id;", ("PING_INSERT", "ping address"))
        new_id = cur.fetchone()[0]
        conn.commit()
        print("Inserted id:", new_id)
        cur.execute("SELECT * FROM businesses WHERE id = %s;", (new_id,))
        print("Row:", cur.fetchone())
    except Exception as e:
        print("ERROR:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_insert()
