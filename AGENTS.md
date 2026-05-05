# Agentia

A blog-native AI agent platform built to learn LangGraph — multi-agent orchestration, RAG knowledge base, and embeddable chat widget. Blog articles are the knowledge source; the embeddable Widget lets readers query them in natural language.

> Read `CONTEXT.md` for the domain glossary before working in this codebase.

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Agent orchestration | LangGraph 0.2+ | Manual `StateGraph` — never `create_react_agent` |
| API | FastAPI + Uvicorn | Async WebSocket + REST |
| LLM | Ollama (`qwen2.5:32b`) + langchain-ollama | Local-first; pluggable via `LLM_PROVIDER` env var |
| Short-term memory (M1) | Redis | Session context, TTL 1hr |
| Long-term memory | PostgreSQL | Messages table + LangGraph `AsyncPostgresSaver` (M2+) |
| Vector search | pgvector (PostgreSQL extension) | `nomic-embed-text` embeddings, 768 dims |
| Observability | structlog + LangGraph Studio + Langfuse (self-hosted) | See Decision 8 in `openspec/changes/agentia/design.md` |
| Frontend | Plain HTML (M1–M2) → React Web Component (M3+) | Shadow DOM, single `<script>` embed |
| Containers | Docker Compose | backend + postgres + redis + langfuse; Ollama on host |

## Architecture

Specs and design live in `openspec/changes/agentia/`. Read them before making structural changes.

### Graph structure (M2+)

```
START → load_context → router
          router ──[chitchat]──────→ agent → save_context → END
          router ──[tool_use]──────→ agent ⇄ tools → save_context → END
          router ──[knowledge_query]→ agent ⇄ tools → save_context → END
          router ──[writing_assist]─→ writing_subgraph → save_context → END
          router ──[clarify]────────→ clarify_node → END
```

### Key decisions (don't reverse without updating `docs/adr/`)

- **Manual `StateGraph`** over `create_react_agent` — every node and edge must be visible for learning
- **`LLMProvider` Protocol** — wraps `ChatOllama`; switch providers via `LLM_PROVIDER=claude` only
- **M1 hand-written Redis memory → M2 `AsyncPostgresSaver`** — intentional two-phase design to surface Context Saturation
- **`astream_events()` not `astream()`** — granular event types (`on_chat_model_stream`, `on_tool_end`)
- **pgvector not Elasticsearch** — reuses existing PostgreSQL, teaches RAG fundamentals without extra infra
- **Langfuse self-hosted** over LangSmith — no trace retention limits, no cost

## Milestones

| Milestone | Goal | Status |
|---|---|---|
| M1 Tracer Bullet | E2E WebSocket chat + Redis memory + plain HTML UI | 🔲 |
| M2 LangGraph Core | Checkpointer + ReAct loop + router + tools + Langfuse | 🔲 |
| M3 Advanced | Human-in-the-loop + FastAPI DI + React Widget | 🔲 |
| M4 Blog Knowledge Base | pgvector RAG + writing assistant subgraph | 🔲 |
| M5 Multi-agent | Supervisor + 4 sub-agents (Q&A, knowledge, writing, newsletter) | 🔲 |

Implementation tasks: `openspec/changes/agentia/tasks.md`

## Development Principles

**KISS** — implement the simplest version that satisfies the spec scenario. No speculative abstractions.

**SOLID** — one node does one thing (SRP). New tools don't modify graph structure (OCP). `LLMProvider` is swappable (DIP).

**No premature abstraction** — three similar lines beat a helper that nobody asked for.

**No silent failures** — LLM errors raise typed `LLMError(code=...)`. Tool exceptions return `ToolMessage` with error, not a crash.

## Conventions

- **Language**: 所有輸出（包含 Agent 回覆與開發溝通）必須限定為 **繁體中文**。
- **Logging**: every log entry via `structlog`, JSON output, always include `thread_id` and `node` within a request
- **Node structure**: each node function takes `AgentState` and returns `AgentState` (partial update)
- **Tools**: decorated with `@tool`, registered at graph compile time — never hardcoded inside nodes
- **Tests**: use `/tdd` skill, vertical slice per behaviour, no mocking of internal collaborators
- **Debugging**: use `/diagnose` skill for hard bugs; LangGraph Studio for graph state inspection
- **Adding agents**: see `openspec/changes/agentia/design.md` — Direction A (tool) / B (subgraph) / C (sub-agent)

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`thehyyu/Agentia`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default Matt Pocock label vocabulary (`needs-triage`, `ready-for-agent`, etc.). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` at root + `docs/adr/`. See `docs/agents/domain.md`.
