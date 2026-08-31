from parser import fetch_rendered_html_with_playwright, extract_clean_page_content, create_text_chunks
import hashlib

def calculate_file_hash_text(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

html1 = fetch_rendered_html_with_playwright("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=units-control-enclosure-replaceable")
text1, _ = extract_clean_page_content(html1)
chunks1 = create_text_chunks(text1, "w1")
h1 = calculate_file_hash_text(chunks1[0]["text"]) if chunks1 else "empty"

html2 = fetch_rendered_html_with_playwright("https://www.ibm.com/docs/en/flashsystem-7x00/8.7.0?topic=flashsystem-7300")
text2, _ = extract_clean_page_content(html2)
chunks2 = create_text_chunks(text2, "w2")
h2 = calculate_file_hash_text(chunks2[0]["text"]) if chunks2 else "empty"

print(f"Hash 1: {h1}")
print(f"Hash 2: {h2}")
print(f"Are they identical chunks? {h1 == h2}")
print(chunks1[0]['text'][:200] if chunks1 else "")
