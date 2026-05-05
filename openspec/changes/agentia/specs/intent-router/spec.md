## ADDED Requirements

### Requirement: Intent classified into five categories via structured output
The router node SHALL classify every user message into one of five intents using LLM structured output (Pydantic model). The output SHALL include `intent` (str) and `confidence` (float 0–1).

Intent categories:
- `chitchat` — general conversation, no external capability needed
- `tool_use` — requires a tool (e.g. get_current_datetime, search_history)
- `knowledge_query` — requires searching the blog knowledge base
- `writing_assist` — requires blog writing assistance (draft, tag, cross-reference)
- `clarify` — message is too ambiguous to route confidently

#### Scenario: Clear chitchat message
- **WHEN** user sends "你好，最近怎樣？"
- **THEN** router returns `intent=chitchat, confidence≥0.8`

#### Scenario: Tool use detected
- **WHEN** user sends "現在幾點？"
- **THEN** router returns `intent=tool_use, confidence≥0.8`

#### Scenario: Knowledge query detected
- **WHEN** user sends "你有寫過關於 LangGraph 的文章嗎？"
- **THEN** router returns `intent=knowledge_query, confidence≥0.8`

#### Scenario: Writing assistance detected
- **WHEN** user sends "幫我起草一篇關於 RAG 的文章"
- **THEN** router returns `intent=writing_assist, confidence≥0.8`

#### Scenario: Ambiguous message routed to clarify
- **WHEN** user sends "幫我"
- **THEN** router returns `intent=clarify, confidence<0.6`

### Requirement: Low-confidence classification routes to clarify
When `confidence` is below 0.6, the graph SHALL route to the clarify node regardless of the classified `intent`, and ask the user to rephrase.

#### Scenario: Low confidence overrides intent
- **WHEN** router returns any intent with `confidence=0.45`
- **THEN** graph routes to clarify node, not to the classified intent's branch

### Requirement: Router output stored in AgentState
The classified `intent` and `confidence` SHALL be written to `AgentState.intent` so downstream nodes can read them without re-invoking the LLM.

#### Scenario: Intent available to subsequent nodes
- **WHEN** router node completes
- **THEN** `AgentState.intent` equals the classified intent string
