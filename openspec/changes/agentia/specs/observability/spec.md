## ADDED Requirements

### Requirement: All log entries carry structured context fields
Every log entry SHALL be emitted via `structlog` in JSON format and SHALL include at minimum: `event` (str), `level` (str), `timestamp` (ISO 8601). Log entries within a request SHALL additionally carry `thread_id` and the current `node` name.

#### Scenario: Node entry logged with context
- **WHEN** any graph node begins execution
- **THEN** a log entry is emitted with `event=node.enter`, `node=<name>`, and `thread_id=<id>`

#### Scenario: LLM response logged with token count
- **WHEN** LLM completes a response
- **THEN** a log entry is emitted with `event=llm.response`, `tokens=<count>`, `duration_ms=<ms>`

#### Scenario: Tool error logged
- **WHEN** a tool raises an exception
- **THEN** a log entry is emitted with `level=error`, `event=tool.failed`, `tool=<name>`, `error=<message>`

### Requirement: Langfuse tracing active when credentials are configured
When `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` environment variables are set, the system SHALL automatically send LLM call traces to the configured Langfuse instance. When they are not set, the system SHALL start normally with no tracing and no errors.

#### Scenario: Tracing enabled with credentials
- **WHEN** both Langfuse env vars are set and a conversation turn completes
- **THEN** a trace record appears in the Langfuse dashboard for that turn

#### Scenario: Tracing disabled without credentials
- **WHEN** Langfuse env vars are absent
- **THEN** application starts and serves requests normally, with no tracing errors in logs

### Requirement: Health check endpoint reports dependency status
`GET /health` SHALL check connectivity to Redis, PostgreSQL, and Ollama and return their individual statuses. If all dependencies are reachable the response code SHALL be 200; if any dependency is unreachable the response code SHALL be 503.

#### Scenario: All dependencies healthy
- **WHEN** Redis, PostgreSQL, and Ollama are all reachable
- **THEN** `GET /health` returns 200 with `{"redis":"ok","postgres":"ok","ollama":"ok"}`

#### Scenario: One dependency unreachable
- **WHEN** Ollama is not running but Redis and PostgreSQL are reachable
- **THEN** `GET /health` returns 503 with `{"redis":"ok","postgres":"ok","ollama":"error: connection refused"}`
