## 1. M1 — 專案基礎建設

- [x] 1.1 初始化 Python 專案結構（`pyproject.toml`、`src/` layout、`.env.example`）
- [x] 1.2 撰寫 `docker-compose.yml`，啟動 PostgreSQL 和 Redis
- [x] 1.3 安裝核心依賴（`fastapi`, `uvicorn`, `langgraph`, `langchain-ollama`, `redis`, `asyncpg`, `structlog`）
- [x] 1.4 建立 PostgreSQL `messages` 表 migration（`id`, `thread_id`, `role`, `content`, `created_at`）
- [x] 1.5 驗證三個依賴連線正常：Redis ping、PostgreSQL SELECT 1、Ollama `/api/tags`

## 2. M1 — Observability 基礎

- [x] 2.1 設定 structlog，輸出 JSON 格式，預設帶 `timestamp` 和 `level`
- [x] 2.2 實作 `GET /health`，檢查 Redis、PostgreSQL、Ollama，回傳 200 或 503

## 3. M1 — LLM Integration

- [x] 3.1 實作 `ChatOllama` 直接呼叫（`qwen2.5:32b`，啟用 streaming）
- [x] 3.2 驗證 streaming：逐 token 印出，確認非一次性回傳

## 4. M1 — Memory Store（手寫層）

- [x] 4.1 實作 Redis context 讀取：`LRANGE session:{thread_id} 0 9`，反序列化為 messages list
- [x] 4.2 實作 Redis context 寫入：`RPUSH` user + assistant，重設 TTL 3600s
- [x] 4.3 實作 PostgreSQL message insert（每 turn 寫入兩筆：user、assistant）
- [x] 4.4 觀察 Context Saturation：對話超過 10 輪後確認 WARN log 出現（`event=context.truncated`）

## 5. M1 — Conversation Engine（單節點）

- [x] 5.1 定義 `AgentState` TypedDict（M1 版：`messages`, `thread_id`）
- [x] 5.2 建立單節點 `StateGraph`：從 Redis 讀 context → 呼叫 Ollama → 回傳 token stream
- [x] 5.3 為每個 graph node 加入 structlog `node.enter` / `node.exit` log

## 6. M1 — Chat API

- [x] 6.1 實作 `WS /ws/chat?thread_id=` WebSocket endpoint
- [x] 6.2 無 `thread_id` 時自動產生 UUID，送 `{type: "session_init", thread_id}` 給 client
- [x] 6.3 串接 `astream_events`，過濾 `on_chat_model_stream`，逐 token 送 WebSocket frame
- [x] 6.4 graph 完成後送 `{type: "turn_end"}` 信號
- [x] 6.5 實作 `GET /api/conversations/{thread_id}`，從 PostgreSQL 回傳歷史訊息

## 7. M1 — Chat UI（純 HTML）

- [x] 7.1 建立 `index.html`，原生 WebSocket 連線，無任何 framework 依賴
- [x] 7.2 實作 token-by-token 渲染（收到 frame 立即 append 至 DOM）
- [x] 7.3 連線時呼叫 `/api/conversations/{thread_id}` 載入歷史訊息
- [x] 7.4 完成標準：傳第二句話時模型記得第一句；重新整理後歷史訊息仍存在

## 8. M2 — LangGraph Checkpointer

- [x] 8.1 安裝 `langgraph-checkpoint-postgres`
- [x] 8.2 將 `AsyncPostgresSaver` 設為 graph checkpointer，以 `thread_id` 為 checkpoint key
- [x] 8.3 移除 M1 手寫 Redis 記憶層（保留 git history 作為對比）
- [x] 8.4 驗證：WebSocket 斷線重連後，對話從中斷點繼續

## 9. M2 — LLM 抽象層

- [x] 9.1 定義 `LLMProvider` Protocol（`invoke`、`astream` 方法）
- [x] 9.2 將 `ChatOllama` 包裝為 `OllamaProvider`
- [x] 9.3 以 `LLM_PROVIDER` 環境變數選擇 provider，預設 `ollama`

## 10. M2 — Intent Router

- [x] 10.1 定義 `IntentClassification` Pydantic model（`intent: str`, `confidence: float`）
- [x] 10.2 實作 router node：呼叫 LLM `with_structured_output(IntentClassification)`
- [x] 10.3 加入 conditional edge：confidence < 0.6 → clarify；否則按 intent 路由
- [x] 10.4 實作 clarify node：回覆請使用者重新描述需求
- [x] 10.5 將 intent 寫入 `AgentState.intent`

## 11. M2 — Conversation Engine（完整 Graph）

- [x] 11.1 擴充 `AgentState`（加入 `intent`, `tool_results`, `iteration_count`）
- [x] 11.2 重建 graph：`START → load_context → router → agent ⇄ tools → save_context → END`
- [x] 11.3 實作 ReAct conditional edge：有 tool call → tools；無 tool call → save_context
- [x] 11.4 實作最大迭代上限（10 次），超過時附加截斷通知並跳出循環

## 12. M2 — Tool System

- [x] 12.1 實作 `get_current_datetime` tool（回傳 ISO 8601 格式，無需參數）
- [x] 12.2 實作 `search_history` tool（PostgreSQL keyword search，回傳最多 5 筆）
- [x] 12.3 確認 tool 拋出例外時，graph 捕捉並回傳 `ToolMessage` 而非 crash
- [x] 12.4 驗證新增 tool 只需加入 tools list，不需修改任何 graph 結構

## 13. M2 — Streaming 與 Observability 升級

- [x] 13.1 更新 `astream_events` handler：區分 `on_chat_model_stream`（送 token）和 `on_tool_end`（log 結果）
- [x] 13.2 安裝 `langfuse`，設定 `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`
- [x] 13.3 驗證 Langfuse dashboard 出現 trace 記錄（含 LLM 輸入輸出、token 數）
- [x] 13.4 啟動 LangGraph Studio，連接本地 graph，確認可視覺化 state 快照

## 14. M3 — Human-in-the-loop

- [ ] 14.1 在 tools node 執行前加入 `interrupt({"tool": name, "args": args})`
- [ ] 14.2 FastAPI 捕捉 interrupt，送 `{type: "confirmation_request", tool, args}` 至 WebSocket
- [ ] 14.3 接收 `{type: "confirmation_response", approved: true/false}` 後呼叫 graph resume
- [ ] 14.4 實作 60 秒 timeout：逾時則跳過 tool，agent 收到 timeout ToolMessage

## 15. M3 — FastAPI Dependency Injection

- [ ] 15.1 將 graph、redis client、db connection 抽出為 FastAPI `Depends()` 函式
- [ ] 15.2 重構 WebSocket endpoint 使用 DI 注入，移除全域狀態

## 16. M3 — Chat Widget（React Web Component）

- [ ] 16.1 初始化 React + Vite 專案（widget 子目錄）
- [ ] 16.2 實作 `<agentia-chat>` Web Component，使用 Shadow DOM 隔離樣式
- [ ] 16.3 實作 token-by-token streaming 渲染
- [ ] 16.4 實作 HITL 確認 dialog UI（顯示 tool 名稱與 args，Confirm / Cancel 按鈕）
- [ ] 16.5 `npm run build` 產出 `widget.js`，嵌入外部測試頁面驗證無樣式衝突

## 17. M4 — pgvector 與 Embedding 設定

- [ ] 17.1 在 PostgreSQL 啟用 `CREATE EXTENSION vector`
- [ ] 17.2 建立 `chunks` 表（`id`, `doc_id`, `content`, `embedding vector(768)`, `created_at`）
- [ ] 17.3 以 `ollama pull nomic-embed-text` 下載本地 embedding 模型
- [ ] 17.4 驗證 Ollama embedding API 回傳 768 維向量

## 18. M4 — 知識庫 Ingestion

- [ ] 18.1 實作 `POST /api/knowledge/ingest` 接受 PDF、TXT、Markdown 上傳
- [ ] 18.2 實作 PDF 解析（`pypdf`）
- [ ] 18.3 實作文字分段（500 token、50 token overlap）
- [ ] 18.4 實作 embedding：每個 chunk 呼叫 Ollama `nomic-embed-text`
- [ ] 18.5 批次 INSERT chunks 至 pgvector 表
- [ ] 18.6 不支援的檔案格式回傳 400

## 19. M4 — Knowledge Retrieval Tool

- [ ] 19.1 實作 `retrieve_knowledge(query)` tool：embed query → cosine search top 5 chunks
- [ ] 19.2 將 retrieved chunks 以 SystemMessage 注入 LLM context（標註「以下為參考資料：」）
- [ ] 19.3 回傳 `related_articles`（最多 3 筆同文件或相似文件標題）
- [ ] 19.4 驗證：上傳一篇 blog 文章 → 問其中的內容 → 模型正確引用原文回答

## 20. M4 — Writing Assistant

- [ ] 20.1 建立 writing-assistant subgraph（retrieve style samples → draft → suggest tags → cross-reference）
- [ ] 20.2 將 `writing_assist` intent 路由至 writing-assistant subgraph
- [ ] 20.3 實作 tag 建議：從現有文章的 tag 詞彙中選出 3–5 個
- [ ] 20.4 實作 cross-reference：搜尋相關舊文章，回傳最多 5 筆標題
- [ ] 20.5 驗證多輪修改：使用者說「讓第二段更簡潔」後 draft 正確更新

## 21. M5 — Agent Supervisor

- [ ] 21.1 建立 Supervisor StateGraph，以 intent 為路由鍵
- [ ] 21.2 將現有 chat graph 包裝為 General Chat Agent subgraph
- [ ] 21.3 將 knowledge retrieval 包裝為 Knowledge Agent subgraph
- [ ] 21.4 將 writing assistant 包裝為 Writing Assistant Agent subgraph
- [ ] 21.5 實作 Newsletter Agent subgraph（取最近 30 天文章 → 合成電子報草稿）
- [ ] 21.6 確認子 agent 錯誤不影響 Supervisor 及其他子 agent
- [ ] 21.7 在 Langfuse trace 加入 `handled_by` 欄位，標記路由至哪個子 agent
- [ ] 21.8 端對端驗證：「幫我整理最近的文章成電子報」→ Newsletter Agent 正確執行
