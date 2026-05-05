## ADDED Requirements

### Requirement: Tools defined with name, description, and input schema
Every tool SHALL be defined as a Python function decorated with `@tool`, providing a name, docstring description, and typed input parameters. The description SHALL be clear enough for the LLM to decide when to call it.

#### Scenario: Tool schema readable by LLM
- **WHEN** the graph is compiled with a tool list
- **THEN** each tool's name and description are included in the LLM's system context

### Requirement: Tool results injected back into AgentState
After a tool executes, its output SHALL be appended to `AgentState.messages` as a `ToolMessage`, making the result available to the agent node on the next iteration.

#### Scenario: Tool result available to agent
- **WHEN** a tool completes execution
- **THEN** `AgentState.messages` contains a new `ToolMessage` with the tool's output before agent is reinvoked

### Requirement: Tool errors caught and returned as error messages
If a tool raises an exception, the system SHALL catch it and return a `ToolMessage` with an error description rather than crashing the graph.

#### Scenario: Tool exception handled gracefully
- **WHEN** a tool raises any exception during execution
- **THEN** agent receives a `ToolMessage` with content describing the error, and the graph continues

### Requirement: New tools addable without modifying graph structure
Adding a new tool SHALL require only defining the function and registering it in the tool list. No node, edge, or conditional function SHALL need to change.

#### Scenario: New tool registered without graph changes
- **WHEN** a new `@tool` function is added to the tools list at graph compile time
- **THEN** the agent can invoke it on the next request without any other code changes

### Requirement: Starter tools — get_current_datetime
The system SHALL include a `get_current_datetime` tool that returns the current date and time in ISO 8601 format. It accepts no parameters.

#### Scenario: Datetime tool returns current time
- **WHEN** agent calls `get_current_datetime`
- **THEN** the result is a string matching ISO 8601 format representing the current local datetime

### Requirement: Starter tools — search_history
The system SHALL include a `search_history` tool that accepts a `keyword` string and searches the current session's message history in PostgreSQL, returning up to 5 matching messages.

#### Scenario: Keyword found in history
- **WHEN** agent calls `search_history(keyword="LangGraph")` and prior messages contain that keyword
- **THEN** the result is a list of up to 5 matching message contents

#### Scenario: Keyword not found in history
- **WHEN** agent calls `search_history(keyword="xyz123")` and no messages match
- **THEN** the result is an empty list, not an error
