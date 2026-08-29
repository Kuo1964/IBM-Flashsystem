import subprocess
import zipfile
import hashlib
import shutil
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF_DIR = BASE_DIR / "raw_data" / "pdfs"
LOCAL_DATA_DIR = Path.home() / ".ibm_flashsystem_kb"
PACKAGES_DIR = LOCAL_DATA_DIR / "downloaded_packages"
PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)

# 官方 COS 離線手冊全集清單
OFFICIAL_PACKAGES = [
    ("9.1.3", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_9.1.3/fs9x00.zip"),
    ("9.1.2", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_9.1.2/fs_9x00.zip"),
    ("9.1.1", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_9.1.1/flashsystem_9x00.zip"),
    ("9.1.0", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_9.1.0/fs9000_910.zip"),
    ("8.7.3", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_8.7.3/FlashSystem_9k_v873.zip"),
    ("8.7.1", "https://ibm-docs-static-content.s3.us.cloud-object-storage.appdomain.cloud/pdx/STSLR9_8.7.1/FlashSystem_9k_v871.zip"),
]

def calculate_sha256(filepath_or_bytes):
    h = hashlib.sha256()
    if isinstance(filepath_or_bytes, bytes):
        h.update(filepath_or_bytes)
    else:
        with open(filepath_or_bytes, "rb") as f:
            while chunk := f.read(8192 * 16):
                h.update(chunk)
    return h.hexdigest()

def download_and_extract_all():
    print("=" * 70)
    print("🚀 啟動 IBM FlashSystem 官方全版本 PDF 文檔包高速獲取與去重...")
    print("=" * 70)

    # 1. 建立現有 PDF 的 SHA-256 雜湊集合
    existing_hashes = {}
    for p in RAW_PDF_DIR.glob("*.pdf"):
        try:
            existing_hashes[calculate_sha256(p)] = p.name
        except Exception:
            pass
    print(f"📊 現有本地 PDF 數量: {len(existing_hashes)} 個")

    # 若 ~/.ibm_flashsystem_kb/fs9x00.zip 存在，直接複製為 9.1.3 快取
    existing_zip = LOCAL_DATA_DIR / "fs9x00.zip"
    cached_913 = PACKAGES_DIR / "9.1.3_fs9x00.zip"
    if existing_zip.exists() and (not cached_913.exists() or cached_913.stat().st_size < 100*1024*1024):
        print("📦 發現本機已下載之 9.1.3 手冊包，直接載入快取...")
        shutil.copy2(existing_zip, cached_913)

    new_pdf_count = 0

    for version, url in OFFICIAL_PACKAGES:
        zip_filename = url.split("/")[-1]
        local_zip = PACKAGES_DIR / f"{version}_{zip_filename}"
        
        # 使用 curl 高速斷點續傳下載
        if not local_zip.exists() or local_zip.stat().st_size < 10*1024*1024:
            print(f"\n📥 正在以 curl 高速下載版本 [{version}] 官方手冊包: {zip_filename}...")
            cmd = ["curl", "-L", "-C", "-", "-o", str(local_zip), url]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if local_zip.exists() and local_zip.stat().st_size > 0:
                mb = local_zip.stat().st_size / (1024 * 1024)
                print(f"✅ 下載完成: {zip_filename} ({mb:.1f} MB)")
            else:
                print(f"❌ 下載失敗 {url}: {res.stderr}")
                continue
        else:
            mb = local_zip.stat().st_size / (1024 * 1024)
            print(f"\n⚡ 已存在本地快取 [{version}]: {zip_filename} ({mb:.1f} MB)")

        # 解壓並進行 SHA-256 去重提取
        try:
            with zipfile.ZipFile(local_zip, "r") as z:
                for member in z.namelist():
                    if member.endswith(".pdf") and not member.startswith("__MACOSX"):
                        pdf_bytes = z.read(member)
                        pdf_hash = calculate_sha256(pdf_bytes)
                        pdf_basename = Path(member).name

                        if pdf_hash in existing_hashes:
                            # 已存在相同內容之 PDF
                            pass
                        else:
                            # 儲存新 PDF
                            target_path = RAW_PDF_DIR / f"{version}_{pdf_basename}"
                            with open(target_path, "wb") as out_f:
                                out_f.write(pdf_bytes)
                            existing_hashes[pdf_hash] = target_path.name
                            new_pdf_count += 1
                            print(f"  ✨ 提取新官方手冊: {target_path.name} ({len(pdf_bytes)/(1024*1024):.1f} MB)")
        except Exception as e:
            print(f"❌ 解析 ZIP 失敗 {local_zip}: {e}")

    print("\n" + "=" * 70)
    print(f"🎉 批量處理完成！新增提取了 {new_pdf_count} 個高價值官方 PDF 手冊。")
    print(f"📚 raw_data/pdfs/ 總計現有官方 PDF 數量: {len(list(RAW_PDF_DIR.glob('*.pdf')))} 個")
    print("=" * 70)

if __name__ == "__main__":
    download_and_extract_all()
