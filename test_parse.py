from curl_cffi import requests
import re, json

res = requests.get("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable", impersonate="chrome110")
html = res.text

iframes = re.findall(r"iframe.*?src=['\"](.*?)['\"]", html)
print("iframes:", iframes)

data = re.search(r"window\.digitalData\s*=\s*(\{.*?\});", html, re.DOTALL)
if data:
    try:
        j = json.loads(data.group(1))
        print("digitalData extracted successfully.")
        print(json.dumps(j, indent=2)[:500])
    except Exception as e:
        print("Error parsing digitalData:", e)

# Also look for any IBM Docs API endpoints in the HTML
apis = re.findall(r"https://www.ibm.com/docs/api/[^\"]+", html)
print("API endpoints found:", list(set(apis)))

