from curl_cffi import requests
res = requests.get("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable", impersonate="chrome110")
html = res.text
print("Replaceable units" in html)
print("03NK55" in html)

import re
json_data = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});", html, re.DOTALL)
if json_data:
    print("Found INITIAL_STATE!")
    
