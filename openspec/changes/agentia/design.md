## Context

Agentia 是 greenfield 學習型專案，無既有程式碼。核心限制：LLM 為本地 Ollama（無雲端 API），所有服務需能一鍵 Docker Compose 啟動。設計決策優先考慮「學習清晰度」，其次才是「最短實作路徑」。

## Goals / Non-Goals

**Goals:**
- 五個里程碑各自獨立可執行，每個里程碑教一組明確的技術概念
- 架構在 M1 完成後可直接延伸至 M2-M5，不需重寫核心

**Non-Goals:**
- 多租戶、Auth、生產級部署（超出學習範圍）
- LlamaIndex 整合（選 pgvector 直接操作以理解原理）
- 效能優化、負載測試

## Decisions

### 1. 手動建 StateGraph vs `create_react_agent`

**選擇：手動 `StateGraph`**

`create_react_agent` 一行完成但黑盒化。手動建圖讓每個 node、edge、conditional function 都可見，是學習 LangGraph 的必要路徑。

Graph 結構（M2 起）：
```
START → load_context → router
          router ──[chitchat]──→ agent → save_context → END
          router ──[tool_use]──→ agent ⇄ tools → save_context → END
          router ──[clarify]───→ clarify_node → END
```

State 型別：
```python
class AgentState(TypedDict):
    messages: list[BaseMessage]
    intent: str
    tool_results: list[dict]
    thread_id: str
```

### 2. LLM 介面：直接呼叫 vs 抽象層

**選擇：薄抽象層（`LLMProvider` Protocol）包裝 `langchain-ollama`**

M1 直接用 `ChatOllama`；M2 起抽出 `LLMProvider` Protocol，讓換 Claude API 只需改 `LLM_PROVIDER=claude` 環境變數，不動 graph 程式碼。

```
LLM_PROVIDER=ollama  →  OllamaProvider(model=qwen2.5:32b, base_url=http://localhost:11434)
LLM_PROVIDER=claude  →  ClaudeProvider(model=claude-sonnet-4-6)  # 日後擴充
```

### 3. M1 手寫記憶 vs 直接用 LangGraph Checkpointer

**選擇：M1 手寫（Redis + PG），M2 換 `AsyncPostgresSaver`**

**核心學習目標：Context Saturation（上下文飽和）**

M1 手寫記憶層的目的不只是「存訊息」，而是讓學習者親身遭遇 Context Window 溢出的問題：當對話歷史不斷累積，傳給 LLM 的 `messages[]` 超過模型 context window 上限時，系統會出錯或品質劣化。學習者必須手動決定策略：

- **截斷（Truncation）**：只保留最近 N 條，最簡單但會失去早期記憶
- **摘要（Summarization）**：把舊訊息壓縮成摘要，保留語意但有失真
- **選擇性保留**：標記重要訊息永久保留，其餘滑動捨棄

M1 刻意讓這個問題浮現，M2 再引入 LangGraph Checkpointer 看框架如何處理相同問題。兩個版本都留在 git history 作為對比。

```
M1: Redis  LRANGE session:{thread_id} 0 9  →  取最近 10 條組成 messages[]
                                               （超過 10 條的舊訊息被截斷）
    PG     INSERT INTO messages (thread_id, role, content)  →  完整歷史持久化

M2: checkpointer = AsyncPostgresSaver(conn)
    graph.compile(checkpointer=checkpointer)
    # LangGraph 透過 thread_config 管理 state 持久化與版本
```

### 4. 串流：`astream()` vs `astream_events()`

**選擇：`astream_events()`**

`astream()` 只回傳 graph state snapshot，無法區分「LLM token」vs「tool 結果」vs「node 完成」。`astream_events()` 回傳具名事件，學習如何過濾 `on_chat_model_stream`、`on_tool_end` 等，是生產用法。

```python
async for event in graph.astream_events(input, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        yield event["data"]["chunk"].content  # token → WebSocket
    elif event["event"] == "on_tool_end":
        log_tool_result(event["data"]["output"])
```

### 5. RAG：pgvector vs Qdrant vs Elasticsearch

**選擇：pgvector（PostgreSQL 擴充）**

pgvector 直接在既有 PostgreSQL 實例上啟用，不需新容器。學習目標是理解 RAG 核心流程（chunking → embedding → similarity search → inject context），pgvector 用熟悉的 SQL 介面完成這件事，不引入新的操作複雜度。

```sql
-- 啟用擴充
CREATE EXTENSION vector;

-- 文件 chunk 表
CREATE TABLE chunks (
    id          uuid PRIMARY KEY,
    doc_id      uuid,
    content     text,
    embedding   vector(768),  -- nomic-embed-text 輸出維度
    created_at  timestamptz
);

-- 相似度搜尋（cosine）
SELECT content
FROM chunks
ORDER BY embedding <=> $1  -- $1 = query embedding
LIMIT 5;
```

Embedding 模型：`nomic-embed-text`（Ollama 本地），768 維，無需外部 API。

日後若需要 hybrid search（語意 + 關鍵字）可加 `tsvector` 欄位或引入 Elasticsearch，不影響現有 schema。

### 6. Human-in-the-loop 實作方式

**選擇：LangGraph `interrupt()` + WebSocket 雙向通道**

```
graph 執行到 tools node
  → interrupt({"action": "confirm", "tool": tool_name, "args": args})
  → FastAPI 把 interrupt payload 送到 WebSocket
  → 前端顯示確認 UI，使用者按確認/取消
  → FastAPI 呼叫 graph.resume(approved=True/False)
  → graph 繼續或跳過 tool
```

### 7. M1 前端：純 HTML vs React

**選擇：M1 純 HTML + 原生 WebSocket API**

M1 目的是驗證後端，不是學前端。一個 `index.html` 無依賴，排除前端建置問題干擾後端 debug。M3 再換 React Web Component。

### 8. 監控與除錯工具組

**選擇：Structlog + LangGraph Studio + Langfuse + Health Check 端點**

四個工具覆蓋不同層的可見度：

**Structlog（應用層 log）**

每條 log 強制帶 context 欄位，出問題時可從 HTTP request 追到 graph node 追到 LLM 呼叫：

```python
log = structlog.get_logger()
log.info("node.enter", node="router", thread_id=thread_id)
log.info("llm.response", node="agent", tokens=150, duration_ms=320)
log.error("tool.failed", tool="retrieve_knowledge", error=str(e))
```

輸出為 JSON，方便 `grep thread_id` 或未來接 log aggregator。

**LangGraph Studio（Graph 本地視覺除錯）**

本地工具，不需 API key。啟動後可在瀏覽器看到：
- Graph 結構（節點、邊、conditional edge 路徑）
- 每次執行時每個 node 的 AgentState 快照
- 重播特定 thread_id 的執行歷程

M1-M2 學習階段最直接的除錯工具，適合看清楚「state 在每個 node 之間怎麼變」。

**Langfuse（LLM 執行追蹤，取代 LangSmith）**

選擇 self-hosted Langfuse 而非 LangSmith，原因：LangSmith 免費 tier 有 trace 數量上限且 14 天後自動刪除，超量需付費。Langfuse 開源、self-hosted，trace 永久保存、完全免費。

```yaml
# docker-compose.yml
langfuse:
  image: langfuse/langfuse
  ports: ["3000:3000"]
  depends_on: [postgres]
```

整合方式：`pip install langfuse`，設 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`，LangGraph callback 自動送 trace。不需要安裝完整 `langchain`，`langchain-core`（已隨 LangGraph 安裝）即可。

**Health Check 端點**

```
GET /health
→ 200 { "redis": "ok", "postgres": "ok", "ollama": "ok" }
→ 503 { "redis": "ok", "postgres": "ok", "ollama": "error: connection refused" }
```

Docker Compose 啟動後第一件事呼叫 `/health`，確認所有依賴都活著再開始開發，避免「為什麼沒回應」的盲目除錯。

## Risks / Trade-offs

| 風險 | 緩解 |
|---|---|
| `qwen2.5:32b`（19GB）在低記憶體機器上跑很慢 | M1/M2 開發時可切換 `mistral:v0.3` 加速迭代 |
| M1 手寫記憶與 M2 Checkpointer 之間有重複工作 | 刻意設計，學習目的；M1 程式碼保留在 git history |
| pgvector 全表掃描在大量 chunk 時變慢 | M4 加 `CREATE INDEX ... USING hnsw`，學習何時需要近似最近鄰索引 |
| `astream_events` v2 API 在 LangGraph 版本間有差異 | 鎖定 `langgraph>=0.2.0`，spec 中記錄版本 |
| Human-in-the-loop WebSocket 狀態管理複雜 | M3 才加入，M1-M2 先不處理；interrupt payload 用 session dict 暫存 |

## Open Questions

- ~~M3 React Web Component 是否需要支援 SSR embed（Next.js 頁面）？~~ **已決定：純 CSR。** Chat widget 為互動元件，不需 SEO，透過 `<script>` 在瀏覽器端載入即可，不受 blog 平台（Next.js、Hugo、WordPress）影響。Script tag 放 `<body>` 底部避免阻塞。
- ~~LangSmith 免費 tier 的 trace 保留天數是否足夠學習使用？~~ **已決定：使用 self-hosted Langfuse，免費且無保留限制。**
- ~~M4 PDF 解析用 `pypdf` 還是 `pymupdf`？~~ **已決定：`pypdf`。** Blog 文章排版簡單，不需要 pymupdf 的複雜解析能力；pypdf MIT license 無限制，pymupdf AGPL-3.0 對外發布時需開源。
- pgvector HNSW index 何時建立？chunk 數量超過多少才值得建？
