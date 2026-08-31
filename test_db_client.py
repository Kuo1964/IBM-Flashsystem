import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_or_create_collection("ibm_flashsystem_kb")
col.add(ids=["test_client"], documents=["test doc"], metadatas=[{"source": "test"}])
print("Client ADD OK")
