from curl_cffi import requests
import re
res = requests.get("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable", impersonate="chrome110")
js_links = re.findall(r'src="([^"]+\.js)"', res.text)
print(js_links)
