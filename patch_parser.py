import re

with open('parser.py', 'r') as f:
    content = f.read()

# Replace the fallback logic so it doesn't silently use the bad HTML
old_logic = """                if len(html_content) < 2000 or "digitalData" in html_content or "ibm.com/docs" in clean_target_url:
                    rendered = fetch_rendered_html_with_playwright(clean_target_url)
                    if rendered:
                        html_content = rendered"""

new_logic = """                if len(html_content) < 2000 or "digitalData" in html_content or "ibm.com/docs" in clean_target_url:
                    rendered = fetch_rendered_html_with_playwright(clean_target_url)
                    if rendered and len(rendered) > 2000:
                        html_content = rendered
                    else:
                        raise Exception("Playwright 渲染失敗或返回空內容，觸發 Rollback")"""

content = content.replace(old_logic, new_logic)

with open('parser.py', 'w') as f:
    f.write(content)

print("Patched parser.py")
