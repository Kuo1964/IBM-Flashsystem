"""
IBM FlashSystem 專家系統 - CLI 本地測試與管理工具
"""

import sys
import argparse
import vector_store
import ingest

def main():
    parser = argparse.ArgumentParser(description="IBM FlashSystem 專家系統 CLI 工具")
    subparsers = parser.add_subparsers(dest="command", help="可執行的子命令")

    # 1. 檢索測試
    query_parser = subparsers.add_parser("query", help="測試查詢專家知識庫")
    query_parser.add_argument("text", type=str, help="查詢問題或關鍵字")
    query_parser.add_argument("--top_k", type=int, default=5, help="返回最相關筆數")

    # 2. 增量更新
    ingest_parser = subparsers.add_parser("ingest", help="執行增量更新掃描")

    # 3. 狀態檢視
    stats_parser = subparsers.add_parser("stats", help="顯示當前知識庫統計資訊")

    args = parser.parse_args()

    if args.command == "query":
        print(f"\n🔍 正在檢索: '{args.text}' (Top {args.top_k}) ...\n")
        results = vector_store.query_kb(query_text=args.text, top_k=args.top_k)
        if not results:
            print("❌ 未找到匹配的技術資料。")
            return
        
        for idx, res in enumerate(results, 1):
            meta = res["metadata"]
            score = res["similarity_score"]
            print(f"[{idx}] 分數: {score:.2f} | 來源: {meta.get('source')} (頁碼 {meta.get('page')})")
            if meta.get("type") == "image_summary":
                print(f"    🖼️ [圖片路徑]: {meta.get('image_path')}")
            print(f"    內容: {res['content'][:150]}...\n")

    elif args.command == "ingest":
        ingest.run_ingestion()

    elif args.command == "stats":
        manifest = ingest.load_manifest()
        pdf_count = sum(1 for v in manifest.values() if v.get("type") == "pdf")
        url_count = sum(1 for v in manifest.values() if v.get("type") == "url")
        print("\n📊 IBM FlashSystem 專家知識庫統計:")
        print(f"  - 已載入紅皮書 (PDF): {pdf_count} 本")
        print(f"  - 已載入網頁連結 (URL): {url_count} 個")
        print(f"  - Manifest 總記錄數: {len(manifest)} 項\n")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
