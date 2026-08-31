import sqlite3
import config

db_path = config.VECTOR_DB_DIR / "chroma.sqlite3"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Find all IDs of non-flashsystem URLs
cursor.execute("""
    SELECT id FROM embedding_metadata 
    WHERE key = 'url' 
    AND string_value NOT LIKE '%flashsystem%' 
    AND string_value NOT LIKE '%sanvolumecontroller%'
""")
invalid_ids = [row[0] for row in cursor.fetchall()]

if invalid_ids:
    print(f"找到 {len(invalid_ids)} 筆不相關的 Chunk 紀錄。準備刪除...")
    
    # SQLite IN clause limits parameters to 999, so we batch them
    batch_size = 500
    for i in range(0, len(invalid_ids), batch_size):
        batch = invalid_ids[i:i+batch_size]
        placeholders = ','.join('?' * len(batch))
        
        cursor.execute(f"DELETE FROM embedding_metadata WHERE id IN ({placeholders})", batch)
        cursor.execute(f"DELETE FROM embeddings WHERE id IN ({placeholders})", batch)
        cursor.execute(f"DELETE FROM embedding_fulltext_search WHERE rowid IN ({placeholders})", batch)
        
    conn.commit()
    cursor.execute("VACUUM")
    print("刪除與空間釋放 (VACUUM) 完成！")
else:
    print("資料庫內沒有發現需要清理的非 FlashSystem 資料。")
    
conn.close()
