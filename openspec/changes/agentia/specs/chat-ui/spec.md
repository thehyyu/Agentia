## ADDED Requirements

### Requirement: M1 — Plain HTML client connects via native WebSocket
The M1 client SHALL be a single `index.html` file with no build step or framework dependency. It SHALL connect to `WS /ws/chat` using the browser's native `WebSocket` API.

#### Scenario: Page opens and connects
- **WHEN** user opens `index.html` in a browser
- **THEN** a WebSocket connection is established to the server automatically

### Requirement: Streaming tokens rendered incrementally
Tokens received from the WebSocket SHALL be appended to the current assistant message in the UI as they arrive, without waiting for the full response.

#### Scenario: Response appears word by word
- **WHEN** user sends a message and LLM begins responding
- **THEN** text appears progressively in the UI as each token frame arrives

### Requirement: Conversation history displayed on load
When the WebSocket connects with an existing `thread_id`, the client SHALL fetch prior messages from `GET /api/conversations/{thread_id}` and render them before accepting new input.

#### Scenario: Prior messages shown on reconnect
- **WHEN** user reopens the chat with an existing `thread_id`
- **THEN** previous messages are displayed in order before the input is enabled

### Requirement: Human-in-the-loop confirmation UI shown on request
When the client receives `{type: "confirmation_request"}`, it SHALL display a confirmation dialog showing the tool name and arguments, with Confirm and Cancel buttons. Input SHALL be disabled until the user responds.

#### Scenario: Confirmation dialog blocks input
- **WHEN** client receives `confirmation_request`
- **THEN** a dialog appears with tool details, and the message input is disabled

#### Scenario: User confirms tool call
- **WHEN** user clicks Confirm in the dialog
- **THEN** client sends `{type: "confirmation_response", approved: true}` and dialog closes

### Requirement: M3 — Chat widget packaged as embeddable Web Component
From M3, the chat UI SHALL be compiled as a Web Component (`<agentia-chat>`) using React and Vite. It SHALL be embeddable on any webpage with a single `<script>` tag and SHALL use Shadow DOM to isolate its styles.

#### Scenario: Widget embedded on external page
- **WHEN** a page includes `<script src="widget.js"></script><agentia-chat></agentia-chat>`
- **THEN** a floating chat button appears and opens the full chat UI when clicked, with no style conflicts with the host page
