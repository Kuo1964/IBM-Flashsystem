import vector_store
collection = vector_store.get_chroma_collection()
res = collection.get(limit=1, include=["embeddings"])
print("Dimension:", len(res["embeddings"][0]) if res["embeddings"] else "Empty collection")
