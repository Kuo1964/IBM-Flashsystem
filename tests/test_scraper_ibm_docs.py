import pytest
import sys
from pathlib import Path

# 將專案根目錄加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser import fetch_rendered_html_with_playwright, extract_clean_page_content

@pytest.mark.timeout(60)
def test_ibm_docs_replaceable_units_parsing():
    url = "https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable"
    
    # 1. 抓取渲染後的 HTML
    html_content = fetch_rendered_html_with_playwright(url)
    assert html_content, "HTML 內容不應為空"
    
    # 2. 解析為 Markdown 與連結
    page_text, links = extract_clean_page_content(html_content)
    assert page_text, "轉換後的 Markdown 文本不應為空"
    
    # 3. 斷言關鍵料號存在 (原先 BeautifulSoup 的 get_text() 無法正確擷取 iframe 內料號)
    assert "03NK551" in page_text or "03JK467" in page_text, f"未能在解析結果中找到預期的 Part Number (03NK551/03JK467)\n截取內容：\n{page_text[:1000]}"
    
    # 4. 斷言表格的 Markdown 語法存在 (原先 BeautifulSoup get_text() 會破壞表格)
    assert "|" in page_text, "未能將表格轉換為 Markdown 格式 (缺少 '|' 符號)"
