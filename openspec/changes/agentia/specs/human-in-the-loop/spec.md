## ADDED Requirements

### Requirement: Graph pauses before tool execution and requests confirmation
Before executing any tool, the graph SHALL call `interrupt()` with a confirmation payload containing the tool name and arguments. Execution SHALL not proceed until the user responds.

#### Scenario: Confirmation request sent to client
- **WHEN** agent decides to call a tool
- **THEN** a WebSocket message of type `confirmation_request` is sent with `{tool, args}` before the tool runs

### Requirement: Graph resumes when user approves
When the user sends an approval response via WebSocket, the graph SHALL resume and execute the tool.

#### Scenario: User approves tool call
- **WHEN** client sends `{type: "confirmation_response", approved: true}`
- **THEN** graph resumes, tool executes, and result is injected into AgentState

### Requirement: Graph skips tool when user rejects
When the user sends a rejection response via WebSocket, the graph SHALL skip the tool and inject a cancellation message into AgentState so the agent can respond accordingly.

#### Scenario: User rejects tool call
- **WHEN** client sends `{type: "confirmation_response", approved: false}`
- **THEN** tool is not executed, agent receives a ToolMessage indicating the action was cancelled by the user

### Requirement: Confirmation times out after 60 seconds
If no confirmation response is received within 60 seconds, the graph SHALL treat it as a rejection and continue without executing the tool.

#### Scenario: Confirmation timeout
- **WHEN** no `confirmation_response` is received within 60 seconds of the `confirmation_request`
- **THEN** tool is skipped and agent receives a ToolMessage indicating timeout
