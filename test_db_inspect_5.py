import sqlite3
import struct
conn = sqlite3.connect("/Users/johnkuo/.ibm_flashsystem_kb/vector_db/chroma.sqlite3")
c = conn.cursor()
c.execute("SELECT embedding FROM embeddings LIMIT 1")
row = c.fetchone()
if row and row[0]:
    # row[0] is bytes, it's a list of float32s
    floats = struct.unpack(f"{len(row[0])//4}f", row[0])
    print("Dimensionality:", len(floats))
else:
    print("No embeddings found!")
conn.close()
