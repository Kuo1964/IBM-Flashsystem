import pickle
with open("/Users/johnkuo/.ibm_flashsystem_kb/vector_db/bf906129-eab8-4814-8b91-02969be215c8/index_metadata.pickle", "rb") as f:
    data = pickle.load(f)
    print("total_elements_added:", data.get("total_elements_added"))
    print("id_to_label count:", len(data.get("id_to_label", {})))
