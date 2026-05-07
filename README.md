# 🤖 Agentia

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1B1F23?style=flat&logo=github&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat)](https://ollama.com/)

> 一個以學習為目的的個人 AI Agent 系統，完整實作 RAG、Multi-agent Supervisor 架構、LangGraph 狀態機、Human-in-the-loop，以及可嵌入任何網頁的 React Web Component。

---

## 🗺️ 系統架構

### 整體流程圖

```mermaid
flowchart TD
    Client([瀏覽器 / Widget]) -->|WebSocket| WS[FastAPI\nWS /ws/chat]
    Client -->|HTTP| REST[FastAPI\nREST Endpoints]

    WS --> Supervisor

    subgraph Supervisor["🎯 Supervisor Graph"]
        R[Router Node\nmistral:v0.3] -->|intent + confidence| Edge{路由決策}
        Edge -->|moon_phase| MPA
        Edge -->|其他 intent| GCA
        Edge -->|confidence < 0.6| Clarify[Clarify Node]

        subgraph GCA["💬 General Chat Agent"]
            LC[load_context] --> AG[Agent Node\nqwen2.5:32b]
            AG -->|has tool_calls| CT[confirm_tool\nHITL]
            CT -->|approved| TN[ToolNode]
            CT -->|cancelled/timeout| AG
            TN --> AG
            AG -->|no tool_calls| SC[save_context]
        end

        subgraph MPA["🌙 Moon Phase Agent"]
            CP[calculate_phase\nephem] --> IP[interpret_phase\nqwen2.5:32b]
        end
    end

    subgraph Tools["🔧 Tool System"]
        T1[get_current_datetime]
        T2[search_history]
        T3[retrieve_knowledge\npgvector RAG]
        T4[web_search\nTavily]
    end

    TN --> Tools

    subgraph Infra["🏗️ Infrastructure"]
        PG[(PostgreSQL\n+ pgvector)]
        RD[(Redis)]
        OL[Ollama\nLocal LLM]
        LF[Langfuse\nObservability]
    end

    GCA --> PG
    GCA --> RD
    AG --> OL
    IP --> OL
    WS -.->|traces| LF
    T3 --> PG
```

### 資料庫 Schema

```mermaid
erDiagram
    messages {
        bigserial id PK
        text thread_id
        text role
        text content
        timestamptz created_at
    }
    chunks {
        bigserial id PK
        text doc_id
        text content
        vector_1024 embedding
        timestamptz created_at
    }
```

---

## ✨ 功能清單（依 Milestone 分組）

### M1 — Tracer Bullet（基礎對話引擎）

- **WebSocket 串流對話**：`WS /ws/chat`，token-by-token 即時回傳
- **Thread 管理**：無 `thread_id` 時自動產生 UUID，送 `session_init` 訊號
- **Redis 短期記憶**：`LRANGE session:{thread_id}` 儲存最近 10 輪對話，TTL 1 小時
- **PostgreSQL 永久歷史**：每輪寫入 `messages` 表，`GET /api/conversations/{thread_id}` 查詢
- **Context Saturation 偵測**：超過 10 輪時觸發 `context.truncated` 警告 log
- **structlog JSON 結構化日誌**：每個 node 發出 `node.enter` / `node.exit`
- **Health Check**：`GET /health` 同時檢查 Redis、PostgreSQL、Ollama 三個依賴

### M2 — LangGraph Core（完整 ReAct 架構）

- **LangGraph Checkpointer**：以 `AsyncPostgresSaver` 替換手寫 Redis 記憶層，斷線重連後對話無縫繼續
- **LLMProvider Protocol**：抽象化 LLM 後端，以 `LLM_PROVIDER` 環境變數切換
- **Intent Router**：LLM structured output 分類使用者意圖（`chitchat` / `tool_use` / `knowledge_query` / `writing_assist` / `moon_phase`），confidence < 0.6 時要求澄清
- **ReAct Loop**：agent node 反覆呼叫 tool 直至無 tool call，最多 10 次迭代
- **Tool System**：新增 tool 只需加入 `ALL_TOOLS` list，不需修改 graph 結構
- **Langfuse 整合**：每次對話產生 trace，記錄 LLM 輸入輸出與 token 數

### M3 — Advanced Interaction（人機協作）

- **Human-in-the-loop (HITL)**：執行非安全 tool 前送 `confirmation_request` 訊號，60 秒逾時自動跳過
- **安全工具白名單**：`retrieve_knowledge`、`web_search`、`get_current_datetime`、`search_history` 不需確認
- **FastAPI Dependency Injection**：graph、db pool、redis 全部透過 `Depends()` 注入，移除全域狀態
- **React Web Component**：`<agentia-chat>` 使用 Shadow DOM 隔離樣式，單 `<script>` 嵌入任何頁面
- **Widget HITL UI**：顯示 tool 名稱與參數的確認 dialog，含 Confirm / Cancel 按鈕

### M4 — Blog Knowledge Base（RAG 知識庫）

- **pgvector 語意搜尋**：`bge-m3` 多語言 embedding 模型（1024 維），支援繁體中文
- **雙語知識攝入**：`POST /api/knowledge/ingest` 同時處理文章的繁中與英文版本
- **文字分段**：500 字 chunk，50 字 overlap，批次寫入 pgvector
- **知識庫同步**：`POST /api/knowledge/sync` 抓取所有 blog 文章與專案，跳過已存在的 slug
- **RAG Tool 優先策略**：系統提示強制 agent 先呼叫 `retrieve_knowledge`，無結果才用 `web_search`
- **Web 搜尋 Fallback**：整合 Tavily API，以 `[來源標題](URL)` 格式回傳

### M5 — Multi-agent Supervisor（多 Agent 架構）

- **Supervisor StateGraph**：頂層 graph 接收 router 的 intent，路由至對應 Sub-agent
- **General Chat Agent Subgraph**：完整的 ReAct loop，含 HITL 與工具系統
- **Moon Phase Agent Subgraph**：以 `ephem` 計算精確月相資料，LLM 生成道家與西方雙詮釋
- **故障隔離**：Moon Phase Agent 錯誤不影響 Supervisor 與 General Chat Agent
- **Langfuse `handled_by` 欄位**：trace 標記路由至哪個 Sub-agent

---

## 🛠️ Tech Stack

| 層次 | 技術 | 用途 |
|------|------|------|
| **Agent 編排** | LangGraph 0.2+ | 手寫 `StateGraph`，每個 node/edge 完全可視 |
| **API 框架** | FastAPI + Uvicorn | Async WebSocket + REST API |
| **LLM（主模型）** | Ollama `qwen2.5:32b` | 本地運行，支援繁體中文，streaming |
| **LLM（Router）** | Ollama `mistral:v0.3` | 輕量 structured output 分類 |
| **Embedding** | Ollama `bge-m3` | 1024 維多語言向量，本地運行 |
| **向量搜尋** | pgvector (PostgreSQL extension) | cosine similarity 搜尋，重用現有 PG infra |
| **短期記憶（M1）** | Redis 7 | Session context，TTL 1 小時 |
| **長期記憶（M2+）** | PostgreSQL + `AsyncPostgresSaver` | LangGraph checkpointer，Thread 持久化 |
| **Observability** | structlog + Langfuse | JSON 結構化 log + LLM trace dashboard |
| **Web 搜尋** | Tavily Python SDK | RAG fallback，知識庫無結果時啟用 |
| **月相計算** | ephem 4.2+ | 精確天文計算，phase name + illumination |
| **前端（M1–M2）** | 純 HTML + 原生 WebSocket | 零依賴，token-by-token DOM 渲染 |
| **前端（M3+）** | React 18 + Vite + TypeScript | Web Component，Shadow DOM 隔離 |
| **容器化** | Docker Compose | PostgreSQL (pgvector image) + Redis |
| **套件管理** | uv | 快速 Python 套件管理與虛擬環境 |

---

## 🏗️ 架構敘述

### 一次對話 Turn 的完整旅程

1. **WebSocket 連線建立**：瀏覽器連接 `WS /ws/chat?thread_id=<uuid>`，若無 thread_id 則 server 自動產生並回送 `session_init`。

2. **Supervisor 接管**：使用者訊息包裝為 `HumanMessage`，注入 `AgentState`，進入頂層 Supervisor Graph。

3. **Intent 分類**：`router` node 使用 `mistral:v0.3` 搭配 `with_structured_output(IntentClassification)` 產生 intent label 與 confidence score。

4. **路由決策**：
   - `moon_phase` → **Moon Phase Agent Subgraph**
   - confidence < 0.6 → **Clarify node**（請使用者重新描述）
   - 其他 intent → **General Chat Agent Subgraph**

5. **General Chat Agent ReAct Loop**：
   - `agent` node 呼叫 `qwen2.5:32b`，根據系統提示決定回答或呼叫 tool
   - 若有 tool_calls → 進入 `confirm_tool` node（HITL）
   - 安全工具直接執行，其他需使用者在 60 秒內確認
   - `ToolNode` 執行 tool，結果作為 `ToolMessage` 回饋給 agent
   - 迭代至無 tool_calls 或達 10 次上限

6. **Moon Phase Agent**：
   - `calculate_phase` node：`ephem` 計算月相名稱、照明度、距新月/滿月天數
   - `interpret_phase` node：LLM 生成道家哲學 + 西方天文民俗雙詮釋

7. **回應串流**：`astream_events()` 過濾 `on_chat_model_stream` 事件，逐 token 送 WebSocket frame；router node 的 token 被 blocklist 過濾，不傳給 client。

8. **持久化**：Turn 結束後，對話寫入 `messages` 表；LangGraph checkpointer 在 PostgreSQL 維護完整 `AgentState` 快照。

### RAG 知識庫流程

```
外部 Blog API ──fetch──→ 文章內容
                          │
                     chunk_text()
                    （500字/50重疊）
                          │
                      embed_text()
                      （bge-m3）
                          │
                  INSERT INTO chunks
                   （pgvector table）
                          │
         retrieve_knowledge tool（查詢時）
                  embed(query) → cosine search top-3
                          │
                  注入 SystemMessage
                 「以下為參考資料：」
                          │
                    LLM 引用回答
```

---

## ⚙️ 環境設定與啟動

### 前置需求

- [uv](https://docs.astral.sh/uv/) — Python 套件管理
- [Docker](https://www.docker.com/) — PostgreSQL + Redis
- [Ollama](https://ollama.com/) — 本地 LLM（需在 host 上運行）

### 1. Clone 並安裝依賴

```bash
git clone https://github.com/thehyyu/Agentia.git
cd Agentia

# 安裝所有依賴（含 M2、M4 optional extras）
uv sync --extra m2 --extra m4
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，填入以下設定：
```

| 環境變數 | 預設值 | 說明 |
|----------|--------|------|
| `LLM_MODEL` | `qwen2.5:32b` | 主模型名稱 |
| `ROUTER_MODEL` | `mistral:v0.3` | Intent router 模型 |
| `LLM_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `DATABASE_URL` | `postgresql+asyncpg://agentia:agentia@localhost:5432/agentia` | PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379` | Redis |
| `LANGFUSE_PUBLIC_KEY` | _(選填)_ | Langfuse observability |
| `LANGFUSE_SECRET_KEY` | _(選填)_ | Langfuse observability |
| `TAVILY_API_KEY` | _(選填)_ | Web 搜尋 fallback |

### 3. 啟動基礎設施

```bash
# 啟動 PostgreSQL（含 pgvector）與 Redis
docker compose up -d

# 確認健康狀態
docker compose ps
```

### 4. 下載 Ollama 模型

```bash
# 主對話模型
ollama pull qwen2.5:32b

# Intent router（較輕量）
ollama pull mistral:v0.3

# Embedding 模型（RAG 用，1024 維多語言）
ollama pull bge-m3
```

### 5. 啟動 API Server

```bash
uv run uvicorn agentia.main:app --reload
```

Server 啟動後開啟 [http://localhost:8000](http://localhost:8000) 即可使用內建 Chat UI。

### 6. 建置 React Widget（選填）

```bash
cd frontend/widget
npm install
npm run build
# 產出 frontend/widget/dist/widget.js
```

嵌入任何 HTML 頁面：

```html
<script src="/widget.js"></script>
<agentia-chat server-url="ws://localhost:8000/ws/chat"></agentia-chat>
```

---

## 🌐 API Endpoints

### HTTP Endpoints

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/health` | 健康檢查，回傳 Redis / PostgreSQL / Ollama 狀態 |
| `GET` | `/api/conversations/{thread_id}` | 查詢指定 Thread 的完整對話歷史 |
| `POST` | `/api/knowledge/ingest` | 攝入單篇文章（body: `{"slug": "...", "type": "post"}` ） |
| `POST` | `/api/knowledge/sync` | 同步所有 blog 文章與專案至知識庫 |

### WebSocket Endpoint

| 路徑 | 說明 |
|------|------|
| `WS /ws/chat?thread_id=<uuid>` | 主對話通道，雙向 JSON frame |

#### WebSocket 訊息格式

**Client → Server：**
```json
{ "type": "chat", "content": "使用者訊息" }
{ "type": "confirmation_response", "approved": true }
```

**Server → Client：**
```json
{ "type": "session_init", "thread_id": "uuid" }
{ "type": "token", "content": "回應文字片段" }
{ "type": "confirmation_request", "tool": "工具名稱", "args": {...} }
{ "type": "turn_end" }
```

---

## 🔧 可用 Tools

| Tool 名稱 | 類型 | 說明 | 需要 HITL 確認 |
|-----------|------|------|----------------|
| `retrieve_knowledge` | RAG | embed query → pgvector cosine search，回傳 top-3 chunks | ❌ 安全工具 |
| `web_search` | 網路搜尋 | Tavily API，5 筆結果（需設定 `TAVILY_API_KEY`） | ❌ 安全工具 |
| `get_current_datetime` | 系統資訊 | 回傳目前 UTC 時間（ISO 8601） | ❌ 安全工具 |
| `search_history` | 資料庫查詢 | PostgreSQL keyword search，回傳最多 5 筆對話記錄 | ❌ 安全工具 |

> 所有現有 tools 均屬安全工具，不觸發 HITL。HITL 機制為未來具有副作用的工具（如寄信、發布文章）預留。

---

## 🧠 關鍵設計決策

### 1. 手寫 `StateGraph` vs `create_react_agent`

刻意不使用 LangGraph 的高階 `create_react_agent` 預設實作，而是完整手寫每個 node 和 conditional edge。目的是讓學習者完全理解狀態機的運作方式，而非把 ReAct loop 當成黑盒子。

### 2. M1 Redis 記憶 → M2 `AsyncPostgresSaver` 兩階段設計

M1 故意使用手寫 Redis 記憶層，並讓 Context Saturation 問題自然浮現（超過 10 輪後記憶遺失）。M2 再以 LangGraph 的 `AsyncPostgresSaver` 解決，讓學習者親身體驗 checkpointer 解決了什麼問題。

### 3. HITL 安全工具 Bypass

`_SAFE_TOOLS` 白名單（`retrieve_knowledge`, `web_search`, `get_current_datetime`, `search_history`）的 tool call 直接跳過 `interrupt()`，不要求使用者確認。這避免了每次 RAG 查詢都需人工審核的使用體驗問題，同時保留 HITL 機制供未來有副作用的工具使用。

### 4. Router Node Token 過濾（Blocklist Streaming）

`process_graph_event()` 中以 `langgraph_node` metadata 過濾掉 `router` node 的 structured output token，確保使用者不會看到 intent 分類的 JSON 輸出。這是多 node graph streaming 常見的必要處理。

### 5. Supervisor 的 Lazy Import（解決循環依賴）

`supervisor.py` 需要 `build_chat_subgraph`（來自 `graph.py`），而 `graph.py` 的 `build_graph` 又呼叫 `build_supervisor`。以 lazy import（函式內部 `from agentia.graph import build_chat_subgraph`）打破循環依賴，同時避免 module-level 初始化問題。

### 6. pgvector vs Elasticsearch

選擇 pgvector 而非獨立的向量資料庫，是因為可直接重用現有 PostgreSQL 實例，減少 infra 複雜度，並且更貼近真實場景（多數中小型應用不需要獨立向量搜尋服務）。

### 7. `astream_events()` vs `astream()`

使用更細粒度的 `astream_events()` API，可以精確分辨 `on_chat_model_stream`（送 token）和 `on_tool_end`（log 結果）兩種事件，而 `astream()` 只給 state snapshot，難以做 token-level streaming。

### 8. LLMProvider Protocol + OllamaProvider 包裝

定義 `LLMProvider` Protocol 而非直接依賴 `ChatOllama`，讓未來切換至 Claude / GPT-4 只需實作同一介面，修改 `LLM_PROVIDER` 環境變數即可。

---

## 📚 我學到了什麼

### LangGraph StateGraph 的真實感受

手寫每個 node 和 edge，讓我深刻理解 LangGraph 的「一切都是 state mutation」設計哲學。Conditional edge 的語意（回傳字串決定下一個 node）一開始很奇怪，但寫多了後非常直覺。

### ReAct Loop 不是魔法

親自實作後才理解 ReAct 其實就是：LLM 輸出 `tool_calls` → 執行 tool → `ToolMessage` 回饋 → LLM 再決策。整個循環就是普通的 while loop 加上 conditional edge。

### Checkpointer 解決的是真實問題

M1 的 Redis 記憶層在 10 輪後會截斷，這不是刻意設計的 bug，而是 Context Saturation 的現實。M2 的 `AsyncPostgresSaver` 不只儲存 messages，而是儲存整個 `AgentState` 快照，斷線重連後 graph 可以從任意 checkpoint 繼續。

### pgvector RAG 的實際限制

embedding 品質決定一切。`bge-m3` 的多語言支援很好，但 chunk 大小（500 字）和 overlap（50 字）的調整需要實際測試，沒有通用最佳值。cosine search top-3 的閾值也需要根據資料集調整。

### Human-in-the-loop 的 UX 設計挑戰

HITL 技術上不難（`interrupt()` + `Command(resume=...)`），但 UX 設計才是重點：什麼工具需要確認？等待時間多長？使用者超時後 agent 如何優雅降級？這些決策比實作本身更複雜。

### Multi-agent 架構的成本

Supervisor 增加了一層 routing，每個 Turn 多一次 LLM 呼叫（router 分類）。對簡單場景來說這是 overhead，但對有明顯分工的系統（對話 vs 計算 vs 知識查詢），清晰的 agent 邊界帶來的可維護性是值得的。

### Shadow DOM Web Component 的隔離性

React 搭配 Shadow DOM 的嵌入方案讓 Widget 真正零 CSS 污染，但也帶來限制：全域字型設定不繼承，debug 時 devtools 需要展開 shadow root。這個 tradeoff 在可嵌入元件場景是標準做法。

---

## 📁 專案結構

```
Agentia/
├── src/agentia/
│   ├── main.py          # FastAPI app + WebSocket endpoint + knowledge API
│   ├── graph.py         # General Chat Agent subgraph + build_graph()
│   ├── supervisor.py    # Supervisor StateGraph + 路由邏輯
│   ├── router.py        # Intent classification node + clarify node
│   ├── moon_phase.py    # Moon Phase Agent subgraph（ephem + LLM）
│   ├── tools.py         # 所有 @tool 函式 + ALL_TOOLS list
│   ├── ingest.py        # RAG ingestion（fetch + chunk + embed）
│   ├── models.py        # AgentState TypedDict
│   ├── llm.py           # LLMProvider Protocol + OllamaProvider
│   ├── events.py        # astream_events 事件處理 + token blocklist
│   ├── hitl.py          # HITL interrupt 解析 + confirmation 等待
│   ├── observability.py # Langfuse callback handler
│   ├── health.py        # Redis / PostgreSQL / Ollama 健康檢查
│   ├── memory.py        # Redis context 讀寫 + PostgreSQL 持久化
│   ├── dependencies.py  # FastAPI Depends() 函式（graph / pool / redis）
│   └── config.py        # 環境變數讀取
├── frontend/
│   ├── index.html       # 原生 HTML Chat UI（M1–M2）
│   └── widget/          # React Web Component（M3+）
│       ├── src/
│       │   ├── main.ts       # AgentiaChat custom element 定義
│       │   ├── ChatApp.tsx   # 主要 React 元件（含 HITL dialog）
│       │   └── types.ts      # WebSocket 訊息型別
│       └── vite.config.ts
├── migrations/
│   ├── 001_init.sql     # messages 表
│   └── 002_pgvector.sql # vector extension + chunks 表
├── tests/               # 50+ 個 pytest 驗收測試
├── openspec/            # 設計文件、任務清單
├── docker-compose.yml   # PostgreSQL (pgvector) + Redis
└── pyproject.toml       # 依賴宣告（uv 管理）
```

---

## 🧪 執行測試

```bash
# 執行所有單元測試（不需外部服務）
uv run pytest

# 執行整合測試（需 PostgreSQL、Redis、Ollama）
uv run pytest -m integration

# 執行特定 milestone 測試
uv run pytest tests/test_task_21*.py -v
```

---
