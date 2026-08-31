import sys, traceback
import vector_store
print("Testing DB insert on 1.5.9 with older Numpy")
fake_chunk = {
    "text": "This is a fake chunk",
    "metadata": {"source": "fake_url", "title": "Fake Title"}
}
try:
    collection = vector_store.get_chroma_collection()
    collection.add(
        ids=["fake_id_777"],
        documents=["fake doc 777"],
        metadatas=[{"source": "fake"}]
    )
    print("DB insert OK")
except Exception as e:
    traceback.print_exc()
