"""
IBM FlashSystem 專家系統 - MCP (Model Context Protocol) 伺服器
提供給 Antigravity, Claude Desktop 或其他 AI Agent 調用的標準工具介面
"""

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer as FastMCP
import vector_store
import ingest
import config

# 初始化 MCP 伺服器
mcp = FastMCP("IBM-FlashSystem-Expert-KB")

@mcp.tool()
def ask_flashsystem_expert(query: str, top_k: int = 25) -> str:
    """
    調用 IBM FlashSystem 頂級架構專家 RAG 中央推理引擎 (Single Source of Truth, SSOT)。
    提供與 Web 客服端 100% 相同之檢索、意圖轉譯、防幻覺約束與官方出處引用解答。
    
    Args:
        query: 客戶或工程師技術提問 (例如: "CMMVC1035E 該怎麼處理" 或 "如何用 CLI 設定 FlashSystem Grid")
        top_k: 檢索最相關之官方技術文檔 Chunks 數量 (預設 25)
    """
    import rag_core
    result = rag_core.process_query(query_text=query, top_k=top_k)
    return result.get("answer", "無法取得專家解答。")

@mcp.tool()
def search_flashsystem_kb(query: str, top_k: int = 5) -> str:
    """
    檢索 IBM FlashSystem 技術專家知識庫。
    包含紅皮書 (Redbooks) 技術內文、規格參數、與 Ollama Vision 提取之 SAN 架構圖與 RAID 技術圖表摘要。
    
    Args:
        query: 查詢問題或關鍵字 (例如: "FlashSystem 9500 拓撲架構" 或 "NVMe-oF 連線規格")
        top_k: 返回的最相關結果筆數 (預設 5)
    """
    results = vector_store.query_kb(query_text=query, top_k=top_k)
    if not results:
        return "未找到與此查詢相關的 IBM FlashSystem 技術資料。"
    
    output_lines = []
    for idx, item in enumerate(results, 1):
        meta = item["metadata"]
        score = item["similarity_score"]
        content = item["content"]
        source = meta.get("source", "未知來源")
        page = meta.get("page", 1)
        item_type = meta.get("type", "text")
        
        entry_header = f"### [檢索結果 {idx}] (相關度分數: {score:.2f}) | 來源: {source}"
        if item_type == "image_summary":
            img_path = meta.get("image_path", "")
            entry_header += f" (第 {page} 頁)\n🖼️ **[技術圖表摘要]** (本地圖片檔: {img_path})"
        elif item_type == "web" or "url" in meta:
            web_url = meta.get("url", source)
            entry_header += f"\n🌐 **[官方線上網頁文檔]** (原始連結: {web_url})"
        else:
            entry_header += f" (第 {page} 頁)"
        
        output_lines.append(f"{entry_header}\n{content}\n")
    
    return "\n" + ("=" * 40) + "\n" + "\n---\n".join(output_lines)

@mcp.tool()
def trigger_kb_ingestion() -> str:
    """
    觸發 IBM FlashSystem 知識庫的檔案掃描與增量更新。
    讀取 raw_data/pdfs/ 內的新 PDF 檔案與 web_urls.txt，執行增量向量化與圖表摘要生成。
    """
    try:
        ingest.run_ingestion()
        return "✅ IBM FlashSystem 專家知識庫增量更新已成功完成！"
    except Exception as e:
        return f"❌ 執行增量更新時發生錯誤: {str(e)}"

@mcp.tool()
def get_kb_stats() -> str:
    """取得當前 IBM FlashSystem 知識庫的統計資訊（包含已處理的紅皮書與網址筆數）"""
    manifest = ingest.load_manifest()
    pdf_count = sum(1 for v in manifest.values() if v.get("type") == "pdf")
    url_count = sum(1 for v in manifest.values() if v.get("type") == "url")
    
    return (
        f"📊 **IBM FlashSystem 專家知識庫狀態報告**\n"
        f"- 向量庫儲存路徑: `{config.VECTOR_DB_DIR}`\n"
        f"- 已處理的紅皮書 (PDF): {pdf_count} 本\n"
        f"- 已處理的網頁連結 (URL): {url_count} 個\n"
        f"- 使用的 Embedding 模型: `{config.EMBEDDING_MODEL}`\n"
        f"- 使用的 Vision 圖表解析模型: `{config.VISION_MODEL}`\n"
    )

if __name__ == "__main__":
    mcp.run()
