"""
IBM FlashSystem 專家系統 - 增量更新與資料吞吐管道 (Ingestion Pipeline)
比對 manifest.json 中的檔案 Hash 值，自動對新增或修改的文件與圖片進行增量向量化處理
"""

import json
from pathlib import Path
from typing import Dict, Any

import config
from parser import parse_pdf, parse_url, calculate_file_hash
from vision_processor import generate_image_summary
from vector_store import add_chunks_to_db, delete_source_from_db

def load_manifest() -> Dict[str, Any]:
    """載入增量記錄檔 manifest.json"""
    if config.MANIFEST_FILE.exists():
        try:
            with open(config.MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[警告] 讀取 manifest.json 失敗: {e}")
    return {}

def save_manifest(manifest: Dict[str, Any]):
    """儲存增量記錄檔 manifest.json"""
    with open(config.MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def run_ingestion():
    """執行全自動增量掃描與資料更新"""
    print("=" * 60)
    print("🚀 開始執行 IBM FlashSystem 知識庫增量掃描與更新作業")
    print("=" * 60)

    manifest = load_manifest()
    updated_count = 0

    # 1. 處理 PDF 紅皮書
    pdf_files = list(config.RAW_PDF_DIR.glob("*.pdf")) + list(config.RAW_PDF_DIR.glob("*.PDF"))
    print(f"[資訊] 掃描到 {len(pdf_files)} 個 PDF 檔案。")

    for pdf_path in pdf_files:
        file_stem = pdf_path.stem
        file_hash = calculate_file_hash(pdf_path)

        # 檢查 Hash 是否變更
        if manifest.get(file_stem, {}).get("hash") == file_hash:
            print(f"  [跳過] 檔案未變更: {pdf_path.name}")
            continue

        print(f"\n📂 正在處理 PDF: {pdf_path.name} ...")
        # 清除資料庫中該來源的舊資料
        delete_source_from_db(file_stem)

        # 解析文字與圖表
        text_chunks, image_records = parse_pdf(pdf_path)
        print(f"  └ 提取到 {len(text_chunks)} 個文字段落，{len(image_records)} 張技術圖表。")

        # 為圖片生成 Vision 多模態摘要
        all_chunks = list(text_chunks)
        for img_rec in image_records:
            img_chunk = generate_image_summary(img_rec)
            if img_chunk:
                all_chunks.append(img_chunk)

        # 寫入向量庫
        add_chunks_to_db(all_chunks)

        # 更新 Manifest
        manifest[file_stem] = {
            "type": "pdf",
            "filename": pdf_path.name,
            "hash": file_hash,
            "chunks_count": len(all_chunks),
            "images_count": len(image_records)
        }
        updated_count += 1

    # 2. 處理網頁 URLs
    if config.RAW_URLS_FILE.exists():
        with open(config.RAW_URLS_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        print(f"\n🌐 掃描到 {len(urls)} 個技術文檔網址。")
        for url in urls:
            url_key = f"url_{url}"
            url_hash = calculate_file_hash_text(url)

            if manifest.get(url_key, {}).get("hash") == url_hash:
                print(f"  [跳過] 網址未變更: {url}")
                continue

            print(f"  🌐 正在抓取並解析網址: {url} ...")
            web_chunks = parse_url(url)
            if web_chunks:
                delete_source_from_db(web_chunks[0]["metadata"]["source"])
                add_chunks_to_db(web_chunks)

                manifest[url_key] = {
                    "type": "url",
                    "url": url,
                    "hash": url_hash,
                    "chunks_count": len(web_chunks)
                }
                updated_count += 1

    # 儲存更新後的 Manifest
    save_manifest(manifest)

    print("\n" + "=" * 60)
    print(f"✅ 增量更新作業完成！共更新 {updated_count} 個項目。")
    print("=" * 60)

def calculate_file_hash_text(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()

if __name__ == "__main__":
    run_ingestion()
