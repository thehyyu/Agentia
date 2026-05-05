# Agentia

A blog-native conversational AI platform. LangGraph orchestrates stateful multi-turn conversations; Ollama runs the LLM locally; pgvector stores blog knowledge for RAG.

## Language

**Turn**:
One complete user message → agent response cycle. A single Thread contains many Turns.
_Avoid_: "message exchange", "round", "conversation step"

**Thread**:
A unique conversation session identified by `thread_id`. Persists across WebSocket reconnections. All Turns in the same Thread share memory.
_Avoid_: "session" (reserved for M1's Redis layer only), "conversation ID"

**Node**:
A single processing unit in the LangGraph StateGraph — e.g. `router`, `agent`, `tools`, `save_context`. Each Node reads and writes AgentState.
_Avoid_: "step", "stage", "handler"

**Graph**:
The compiled LangGraph `StateGraph` that orchestrates one full Turn. The Graph contains Nodes connected by edges and conditional edges.
_Avoid_: "pipeline", "chain", "workflow"

**AgentState**:
The `TypedDict` passed between all Nodes within one Graph execution. Fields: `messages`, `intent`, `tool_results`, `thread_id`, `iteration_count`.
_Avoid_: "context dict", "state object", "payload"

**Intent**:
The classified user goal produced by the router Node. One of: `chitchat`, `tool_use`, `knowledge_query`, `writing_assist`, `clarify`. Stored in `AgentState.intent`.
_Avoid_: "category", "label", "type"

**Tool**:
A Python function decorated with `@tool` that the agent Node can invoke during the ReAct loop. Tools are registered at Graph compile time; adding a Tool does not require changing the Graph structure.
_Avoid_: "function", "action", "capability"

**ReAct Loop**:
The cycle where the agent Node decides to call a Tool or produce a final response. Repeats until no Tool call is present or the iteration limit (10) is reached.
_Avoid_: "agent loop", "tool loop"

**Checkpoint**:
LangGraph's `AsyncPostgresSaver`-backed persisted snapshot of AgentState, keyed by `thread_id`. Introduced in M2, replacing the M1 hand-written memory layer.
_Avoid_: "saved state", "snapshot" (too generic)

**Context Saturation**:
The condition where accumulated Turn history exceeds the LLM's context window budget, degrading response quality or causing errors. Deliberately surfaced in M1 to motivate the Checkpoint design in M2.
_Avoid_: "context overflow", "token overflow", "memory full"

**Provider**:
The LLM backend abstraction (`LLMProvider` Protocol). Currently `OllamaProvider` wrapping `qwen2.5:32b`. Switching providers requires only changing the `LLM_PROVIDER` environment variable.
_Avoid_: "model" (refers to the specific model name, not the interface), "LLM backend"

**Chunk**:
A text segment produced by splitting a document during RAG ingestion (~500 tokens with 50-token overlap). Each Chunk is embedded and stored in pgvector.
_Avoid_: "fragment", "passage", "segment"

**Subgraph**:
A compiled LangGraph Graph used as a Node inside a parent Graph (Direction B). The parent Graph treats it as an opaque unit.
_Avoid_: "nested graph", "child graph"

**Supervisor**:
The M5 top-level agent that receives Intent from the router and delegates execution to the appropriate Sub-agent. Distinct from the router Node, which only classifies; the Supervisor actually routes control flow.
_Avoid_: "orchestrator", "router" (router is the classification Node; Supervisor is the delegation layer)

**Sub-agent**:
A specialised Subgraph managed by the Supervisor. Current Sub-agents: General Chat, Knowledge, Writing Assistant, Newsletter.
_Avoid_: "child agent", "worker agent"

**Widget**:
The embeddable React Web Component (`<agentia-chat>`) packaged as `widget.js`. Embedded on any page with a single `<script>` tag. Uses Shadow DOM to isolate styles.
_Avoid_: "chat UI" (too vague), "embed", "frontend component"

**Milestone**:
One of the five development phases (M1–M5), each independently executable and demonstrable. M1 = Tracer Bullet, M2 = LangGraph Core, M3 = Advanced Interaction, M4 = Blog Knowledge Base, M5 = Multi-agent System.
_Avoid_: "phase", "sprint", "version"

## Relationships

- A **Thread** contains many **Turns**
- A **Turn** is processed by one **Graph** execution
- A **Graph** contains multiple **Nodes** connected by edges
- **Nodes** read and write **AgentState**
- The router **Node** writes **Intent** to **AgentState**
- The agent **Node** runs the **ReAct Loop**, invoking **Tools** as needed
- A **Checkpoint** persists **AgentState** across **Thread** reconnections (M2+)
- A **Subgraph** is used as a **Node** in a parent **Graph** (M4+)
- The **Supervisor** routes **Intent** to **Sub-agents** (M5)
- The **Widget** connects to the Chat API via WebSocket, scoped to one **Thread**

## Flagged ambiguities

- **"context"** alone is ambiguous — could mean AgentState, context window, or session context. Use the specific term instead.
- **"agent"** alone is ambiguous in M5 — use "agent Node" for the ReAct node inside the Graph, "Sub-agent" for Supervisor-managed subgraphs.
- **"session"** is reserved for M1's Redis-backed short-term memory layer only. In M2+, use **Thread** and **Checkpoint** instead.
- **"router"** refers specifically to the intent-classification Node inside the Graph. Do not use it to mean the Supervisor's delegation logic.
