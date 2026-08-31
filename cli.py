"""
IBM FlashSystem 專家系統 - CLI 本地測試與管理工具
"""

import sys
import argparse
import vector_store
import ingest
import rag_core

def main():
    parser = argparse.ArgumentParser(description="IBM FlashSystem 專家系統 CLI 工具")
    subparsers = parser.add_subparsers(dest="command", help="可執行的子命令")

    # 1. 檢索測試
    query_parser = subparsers.add_parser("query", help="測試查詢專家知識庫")
    query_parser.add_argument("text", type=str, help="查詢問題或關鍵字")
    query_parser.add_argument("--top_k", type=int, default=5, help="返回最相關筆數")

    # 2. 增量更新
    ingest_parser = subparsers.add_parser("ingest", help="執行增量更新掃描")
    ingest_parser.add_argument("--force-url", action="store_true", help="強制重新抓取與解析所有技術網頁 (不跳過)")
    ingest_parser.add_argument("--depth", type=int, default=3, help="網頁子連結遞迴抓取最大深度 (預設 3 層)")
    ingest_parser.add_argument("--max-pages", type=int, default=100, help="每個入口網頁最多抓取子頁面數 (預設 100 頁)")

    # 3. 狀態檢視
    stats_parser = subparsers.add_parser("stats", help="顯示當前知識庫統計資訊")

    args = parser.parse_args()

    if args.command == "query":
        print(f"\n🔍 正在使用中央零差別 RAG 核心檢索: '{args.text}' (Top {args.top_k}) ...\n")
        res = rag_core.process_query(query_text=args.text, top_k=args.top_k)
        
        sources = res.get("sources", [])
        answer = res.get("answer", "")
        
        if not sources:
            print("❌ 未找到匹配的技術資料。")
            return
        
        for idx, src in enumerate(sources, 1):
            print(f"[{idx}] 分數: {src['score']:.2f} | 來源: {src['source']} (頁碼 {src['page']})")
        
        print("\n=================== 資深專家解答 ===================")
        print(answer)
        print("===================================================\n")

    elif args.command == "ingest":
        ingest.run_ingestion(force_url=args.force_url, max_depth=args.depth, max_pages=args.max_pages)

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
