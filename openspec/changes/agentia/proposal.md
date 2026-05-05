## Why

Agentia 有兩個互相強化的目標：

**學習目標**：系統性掌握 LangGraph、FastAPI 與本地 LLM 整合的核心概念，每個 capability 對應一個明確的學習主題。

**產品目標**：把 Agentia 嵌入自己的 blog，讓讀者能用自然語言與 blog 內容互動——搜尋文章、取得推薦、提問——同時讓作者擁有 AI 寫作輔助工具。Blog 文章是知識庫的資料來源，也是驗證整套系統的真實場景。

## What Changes

專案分五個里程碑，每個里程碑獨立可執行、可展示：

- **M1 Tracer Bullet**：驗證所有架構層能 E2E 串通——使用者送訊息、LLM 串流回應、對話記憶正確保存；親身遭遇並處理 Context Saturation（上下文飽和）問題
- **M2 LangGraph 核心**：引入原生記憶管理、意圖路由、工具呼叫循環、串流事件處理、執行追蹤
- **M3 進階互動**：加入人工確認機制、重構 API 依賴注入、提供可嵌入 blog 的聊天 Widget
- **M4 Blog 知識庫 Agent**（Direction A + B）：blog 文章作為 RAG 知識庫，讓 agent 能回答讀者問題、推薦相關文章；寫作助手 agent 以現有文章為風格參考輔助起草新文
- **M5 Multi-agent Blog 系統**（Direction C）：Supervisor agent 統一路由，子 agent 各司其職——讀者 Q&A agent、內容推薦 agent、寫作助手 agent、Newsletter 生成 agent

## Capabilities

### New Capabilities

- `conversation-engine`: 管理多輪對話狀態與流程的核心執行時期
- `llm-integration`: 本地 LLM 的統一存取介面，支援串流輸出；可插拔設計供日後切換模型提供者
- `memory-store`: 對話短期 session 記憶與長期歷史的儲存和讀取
- `intent-router`: 識別使用者意圖並決定對話走向的分類機制
- `tool-system`: 讓 agent 能呼叫外部能力並將結果注回對話的工具執行框架
- `human-in-the-loop`: 在關鍵決策點暫停 agent、等待使用者確認後再繼續的控制機制
- `observability`: 多層可觀測性——結構化應用層日誌、graph 視覺化除錯、LLM 執行追蹤、依賴健康檢查
- `chat-api`: 供前端接入的即時對話 API
- `chat-ui`: 可嵌入任何網頁的聊天介面
- `knowledge-retrieval`: blog 文章的 RAG 管線——文章索引、語意搜尋、相關文章推薦
- `writing-assistant`: 以現有 blog 文章為風格基礎，輔助起草新文、建議標籤、找出可交叉引用的舊文章
- `agent-supervisor`: Supervisor 模式——接收使用者意圖後路由至對應的專門子 agent（M5）

### Modified Capabilities

_(none — greenfield project)_

## Impact

新引入的系統與依賴：

| 類別 | 技術 |
|---|---|
| Agent 編排 | LangGraph |
| API 服務 | FastAPI + Uvicorn |
| 本地 LLM | Ollama |
| 關聯式資料庫 | PostgreSQL |
| 快取 / 訊息 | Redis |
| 向量搜尋 | pgvector（PostgreSQL 擴充）|
| 執行追蹤 | Langfuse（self-hosted）|
| 前端 | React（Web Component）|
| 容器化 | Docker Compose |

**No existing code is modified** (greenfield).
