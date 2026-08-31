import sys, traceback
import vector_store
print("Testing DB insert on 1.5.9 with Numpy 2.5.1")
fake_chunk = {
    "text": "This is a fake chunk",
    "metadata": {"source": "fake_url", "title": "Fake Title"}
}
try:
    collection = vector_store.get_chroma_collection()
    collection.add(
        ids=["fake_id_999"],
        documents=["fake doc 999"],
        metadatas=[{"source": "fake"}]
    )
    print("DB insert OK")
except Exception as e:
    traceback.print_exc()
