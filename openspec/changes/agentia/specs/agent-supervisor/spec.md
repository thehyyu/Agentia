## ADDED Requirements

### Requirement: Supervisor routes requests to specialised sub-agents
The Supervisor SHALL receive the classified intent from the router and delegate the request to the appropriate sub-agent. Each sub-agent is an independently compiled LangGraph subgraph.

Sub-agent mapping:
- `chitchat` / `tool_use` → General Chat Agent
- `knowledge_query` → Knowledge Agent (RAG-enabled)
- `writing_assist` → Writing Assistant Agent
- Newsletter generation (explicit request) → Newsletter Agent

#### Scenario: Knowledge query routed to Knowledge Agent
- **WHEN** intent is `knowledge_query`
- **THEN** Supervisor delegates to the Knowledge Agent subgraph and returns its response

#### Scenario: Writing request routed to Writing Assistant Agent
- **WHEN** intent is `writing_assist`
- **THEN** Supervisor delegates to the Writing Assistant Agent subgraph and returns its response

### Requirement: Each sub-agent operates independently
Each sub-agent SHALL have its own internal graph, state, and tool set. A failure in one sub-agent SHALL not affect the Supervisor or other sub-agents.

#### Scenario: Sub-agent error isolated
- **WHEN** the Knowledge Agent raises an internal error
- **THEN** the Supervisor catches the error, returns an error message to the user, and remains available for subsequent requests

### Requirement: Newsletter Agent synthesises recent posts on request
When the user explicitly requests a newsletter draft, the Supervisor SHALL invoke the Newsletter Agent, which retrieves the most recent blog posts from the knowledge base and synthesises them into a newsletter-ready summary.

#### Scenario: Newsletter drafted from recent posts
- **WHEN** user requests "幫我整理最近的文章成電子報"
- **THEN** Newsletter Agent retrieves posts from the last 30 days and produces a structured newsletter draft with intro, article summaries, and closing

### Requirement: Supervisor response includes sub-agent attribution
The final response SHALL indicate which sub-agent handled the request, enabling the developer to trace routing decisions in Langfuse.

#### Scenario: Attribution included in trace
- **WHEN** a turn completes via any sub-agent
- **THEN** the Langfuse trace contains a `handled_by` field identifying the sub-agent name
