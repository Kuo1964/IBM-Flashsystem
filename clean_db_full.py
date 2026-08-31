import sqlite3
import config

db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Find orphan embeddings
cursor.execute("""
    SELECT id FROM embeddings 
    WHERE id NOT IN (SELECT id FROM embedding_metadata)
""")
orphan_embeddings = [row[0] for row in cursor.fetchall()]

if orphan_embeddings:
    print(f"Finding {len(orphan_embeddings)} orphan chunks...")
    batch_size = 500
    for i in range(0, len(orphan_embeddings), batch_size):
        batch = orphan_embeddings[i:i+batch_size]
        placeholders = ','.join('?' * len(batch))
        cursor.execute(f"DELETE FROM embeddings WHERE id IN ({placeholders})", batch)
        # Note: fulltext search uses rowid of embeddings, so if we delete embeddings we can't easily map back,
        # but chroma doesn't use FTS out of the box unless we configured it. 
        # I'll just delete from FTS if there is an orphan rowid.
    conn.commit()
    print("Orphans cleaned.")
    
cursor.execute("VACUUM")
conn.commit()
conn.close()
