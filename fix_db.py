import sqlite3
import sys

db_path = "raw_data/chroma_db/chroma.sqlite3"
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check max seq_id in embeddings queue
    c.execute("SELECT seq_id FROM embeddings_queue ORDER BY seq_id DESC LIMIT 1")
    row = c.fetchone()
    print("embeddings_queue max seq_id:", type(row[0]) if row else "None", row)
    
    # Check max seq_id in collections
    c.execute("SELECT * FROM max_seq_id")
    row = c.fetchone()
    print("max_seq_id table:", row)
    conn.close()
except Exception as e:
    print("Error:", e)
