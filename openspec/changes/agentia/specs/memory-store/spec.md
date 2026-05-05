## ADDED Requirements

### Requirement: M1 — Session context loaded from Redis before each turn
The system SHALL retrieve the most recent 10 messages for a given `thread_id` from Redis before passing them to the LLM. Messages SHALL be stored as JSON-serialised `{role, content}` objects.

#### Scenario: Existing session context retrieved
- **WHEN** a message arrives for a `thread_id` that has prior messages in Redis
- **THEN** the last 10 messages are prepended to the current input before LLM invocation

#### Scenario: New session starts empty
- **WHEN** a message arrives for a `thread_id` with no Redis entry
- **THEN** only the current message is sent to the LLM

### Requirement: M1 — Context window saturation handled by truncation
When the accumulated messages exceed 10 entries, the system SHALL drop the oldest messages, retaining only the most recent 10. This truncation SHALL be logged so the developer can observe context saturation occurring.

#### Scenario: Context truncated after 10 messages
- **WHEN** Redis list for `thread_id` contains more than 10 messages
- **THEN** only the 10 most recent are loaded into AgentState, and a log entry with level WARN is emitted with field `event=context.truncated`

### Requirement: M1 — Each turn appended to Redis with TTL
After every completed turn the system SHALL append both the user message and assistant response to the Redis list for that `thread_id`. The list TTL SHALL be reset to 3600 seconds on every write.

#### Scenario: Messages persisted after turn
- **WHEN** a turn completes successfully
- **THEN** Redis list for `thread_id` contains the new user and assistant messages, and TTL is 3600 seconds

### Requirement: M1 — All messages persisted to PostgreSQL
Every user message and assistant response SHALL be written to the `messages` table with columns: `id`, `thread_id`, `role`, `content`, `created_at`. PostgreSQL is the complete history; Redis is the hot context window.

#### Scenario: Both messages written to database
- **WHEN** a turn completes
- **THEN** exactly two new rows exist in `messages` for that turn (role=user, role=assistant), with correct `thread_id` and `created_at`

### Requirement: M2 — LangGraph AsyncPostgresSaver replaces hand-written memory
From M2 onward the system SHALL use `AsyncPostgresSaver` as the LangGraph graph checkpointer. The hand-written Redis layer SHALL be removed. State persistence and retrieval SHALL be handled entirely by the checkpointer using `thread_id` as the checkpoint key.

#### Scenario: Conversation resumed via checkpointer
- **WHEN** a WebSocket reconnects with the same `thread_id`
- **THEN** graph state is restored from the PostgreSQL checkpoint and conversation continues from where it left off

### Requirement: Sessions are isolated by thread_id
State from one `thread_id` SHALL never be readable or writable by operations scoped to a different `thread_id`.

#### Scenario: Cross-session isolation
- **WHEN** two concurrent sessions use different `thread_id` values
- **THEN** each session's messages and checkpointed state are completely independent
