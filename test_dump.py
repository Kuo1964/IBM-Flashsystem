from curl_cffi import requests
res = requests.get("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable", impersonate="chrome110")
with open("ibm_docs.html", "w") as f:
    f.write(res.text)
print("Dumped.")
