import time
from seleniumbase import Driver

def test_ibm_docs():
    print("啟動 SeleniumBase (UC Mode)...")
    try:
        driver = Driver(uc=True, headless=True)
        url = "https://www.ibm.com/docs/en/flashsystem-9x00/9.1.3?topic=software-feature-guide"
        print(f"正在前往: {url}")
        
        driver.get(url)
        time.sleep(5)  # 等待 JS 渲染
        
        html = driver.page_source
        print(f"成功取得網頁原始碼，長度: {len(html)} 字元")
        
        if "Request to GET" in html and "not allowed by policy" in html:
            print("❌ 失敗：被 WAF 阻擋 (403 Forbidden)")
        elif "digitalData" in html or "IBM" in html:
            print("✅ 成功繞過 WAF 取得內容！")
        
        driver.quit()
    except Exception as e:
        print(f"執行時發生錯誤: {e}")

if __name__ == "__main__":
    test_ibm_docs()
