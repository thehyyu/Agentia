## ADDED Requirements

### Requirement: LLM streams tokens as they are generated
The integration SHALL yield tokens incrementally as the LLM produces them, not buffer and return all at once.

#### Scenario: Streaming response delivered token by token
- **WHEN** a prompt is sent to the LLM
- **THEN** each token is yielded to the caller as soon as it is generated

### Requirement: System prompt is configurable per-request
The integration SHALL accept an optional `system_prompt` parameter on each invocation. If not provided, a default system prompt SHALL be used.

#### Scenario: Custom system prompt overrides default
- **WHEN** caller passes a non-empty `system_prompt`
- **THEN** the LLM receives that string as the system message

#### Scenario: Default system prompt used when none provided
- **WHEN** caller passes no `system_prompt`
- **THEN** the LLM receives the configured default system message

### Requirement: LLM provider is switchable via environment variable
The integration SHALL read `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_BASE_URL` from environment at startup. Changing these values SHALL switch providers without modifying application code.

#### Scenario: Ollama provider loaded from environment
- **WHEN** `LLM_PROVIDER=ollama` and `LLM_BASE_URL=http://localhost:11434`
- **THEN** all LLM calls are routed to local Ollama instance

### Requirement: LLM errors are surfaced as typed exceptions
The integration SHALL catch provider-level errors (connection refused, model not found, context length exceeded) and raise a typed `LLMError` with a `code` field, not raw HTTP exceptions.

#### Scenario: Ollama not running
- **WHEN** Ollama process is not running and a prompt is sent
- **THEN** `LLMError(code="connection_refused")` is raised
