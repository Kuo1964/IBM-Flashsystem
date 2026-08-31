import pickle
import sys

# Get metadata file path
with open("/Users/johnkuo/.ibm_flashsystem_kb/vector_db/518b54fb-4232-4b52-a157-ba8080688df8/header.bin", "rb") as f:
    data = pickle.load(f)
    print("KEYS:", data.keys() if isinstance(data, dict) else "Not dict")
    if isinstance(data, dict):
        for k, v in data.items():
            print(k, ":", type(v))
