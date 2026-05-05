## ADDED Requirements

### Requirement: WebSocket endpoint accepts chat connections
The system SHALL expose a WebSocket endpoint at `WS /ws/chat` that accepts a `thread_id` query parameter. Each connection maps to one LangGraph session identified by that `thread_id`.

#### Scenario: Client connects with thread_id
- **WHEN** client opens `WS /ws/chat?thread_id=abc123`
- **THEN** connection is established and the graph session for `abc123` is ready to receive messages

#### Scenario: Client connects without thread_id
- **WHEN** client opens `WS /ws/chat` with no `thread_id` parameter
- **THEN** server generates a new UUID as `thread_id` and sends it to the client as `{type: "session_init", thread_id: "<uuid>"}`

### Requirement: LLM tokens streamed to client as they arrive
The system SHALL forward each token from `astream_events` `on_chat_model_stream` events to the client as a WebSocket text frame immediately upon receipt, without buffering.

#### Scenario: Tokens delivered incrementally
- **WHEN** LLM generates a response
- **THEN** client receives multiple WebSocket frames, each containing one or a few tokens, before the full response is complete

### Requirement: Stream completion signalled to client
When the graph finishes a turn the system SHALL send a `{type: "turn_end"}` message so the client knows the response is complete.

#### Scenario: Turn end signal sent
- **WHEN** graph reaches END for a turn
- **THEN** client receives `{type: "turn_end"}` after the last token frame

### Requirement: Human-in-the-loop confirmation routed through WebSocket
When the graph issues an `interrupt()`, the system SHALL send `{type: "confirmation_request", tool: "<name>", args: {…}}` to the client and suspend streaming until a `confirmation_response` is received.

#### Scenario: Confirmation request pauses stream
- **WHEN** graph calls interrupt before a tool
- **THEN** streaming stops and client receives `{type: "confirmation_request", tool: "<name>", args: {…}}`

#### Scenario: Confirmation response resumes stream
- **WHEN** client sends `{type: "confirmation_response", approved: true}`
- **THEN** graph resumes and token streaming continues

### Requirement: REST endpoint for conversation history
`GET /api/conversations/{thread_id}` SHALL return all messages for that `thread_id` from PostgreSQL in chronological order, as a JSON array of `{role, content, created_at}` objects.

#### Scenario: History returned for existing thread
- **WHEN** `GET /api/conversations/abc123` is called and messages exist
- **THEN** response is 200 with a JSON array ordered by `created_at` ascending
