import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

options = uc.ChromeOptions()
options.add_argument('--headless')
driver = uc.Chrome(options=options)
driver.get("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable")
time.sleep(5)
html = driver.page_source
print("403 Forbidden" in html)
print("Replaceable units" in html)
driver.quit()
