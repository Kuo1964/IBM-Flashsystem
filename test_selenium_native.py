import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
driver.get("https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=software-feature-guide")
time.sleep(5)
html = driver.page_source
print("HTML Length:", len(html))
if "not allowed by policy" in html:
    print("Failed: Blocked by WAF")
elif "digitalData" in html:
    print("Success! Got IBM Docs Content.")
else:
    print("Unknown response")
driver.quit()
