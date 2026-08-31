import vector_store
print("Testing DB ADD...")
fake_chunk = {
    "text": "This is a fake chunk for adding",
    "metadata": {"source": "fake_url", "title": "Fake Title"}
}
vector_store.add_chunks_to_db([fake_chunk])
print("DB ADD OK")
