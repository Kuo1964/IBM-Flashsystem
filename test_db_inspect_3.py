import pickle
with open("/Users/johnkuo/.ibm_flashsystem_kb/vector_db/bf906129-eab8-4814-8b91-02969be215c8/index_metadata.pickle", "rb") as f:
    data = pickle.load(f)
    print("KEYS:", data.keys() if isinstance(data, dict) else type(data))
    if isinstance(data, dict):
        for k, v in data.items():
            print(k, ":", type(v))
