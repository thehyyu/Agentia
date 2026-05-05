## ADDED Requirements

### Requirement: Graph maintains typed conversation state across nodes
The system SHALL represent every conversation as a `AgentState` TypedDict passed through all graph nodes. State MUST contain: `messages` (list of BaseMessage), `intent` (str), `tool_results` (list of dict), `thread_id` (str).

#### Scenario: State flows through all nodes unchanged unless explicitly mutated
- **WHEN** a node receives `AgentState`
- **THEN** only the fields that node is responsible for are updated; all other fields remain identical

### Requirement: Graph executes ReAct loop between agent and tools
The agent node SHALL decide on each invocation whether to call a tool or produce a final response. If a tool call is present in the LLM output, graph SHALL route to the tools node and back to agent. This loop SHALL continue until agent produces a response with no tool calls.

#### Scenario: Agent calls one tool then responds
- **WHEN** agent output contains one tool call
- **THEN** graph routes to tools node, executes the tool, returns to agent, and agent produces final response with no further tool calls

#### Scenario: Agent responds directly without tools
- **WHEN** agent output contains no tool calls
- **THEN** graph routes directly to save_context then END

#### Scenario: Agent calls multiple tools across turns
- **WHEN** agent output contains a tool call and after tool result agent calls another tool
- **THEN** loop repeats until agent output contains no tool calls

### Requirement: Graph enforces maximum loop iterations
The graph SHALL halt the ReAct loop after 10 agent-tools cycles and return whatever partial response exists, to prevent infinite loops.

#### Scenario: Loop limit reached
- **WHEN** agent-tools cycle count reaches 10
- **THEN** graph exits loop and routes to save_context with a truncation notice appended to messages
