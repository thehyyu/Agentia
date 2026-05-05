## ADDED Requirements

### Requirement: Blog articles ingested via upload endpoint
`POST /api/knowledge/ingest` SHALL accept a file upload (PDF, TXT, or Markdown). The system SHALL parse the file, split it into chunks of approximately 500 tokens with 50-token overlap, embed each chunk using the local Ollama embedding model, and store the chunks in the `chunks` table in PostgreSQL with pgvector.

#### Scenario: PDF article ingested successfully
- **WHEN** a PDF file is uploaded to `/api/knowledge/ingest`
- **THEN** the response is 200, and the `chunks` table contains new rows for that document with non-null `embedding` vectors

#### Scenario: Unsupported file type rejected
- **WHEN** a `.docx` file is uploaded
- **THEN** the response is 400 with an error message listing supported formats

### Requirement: Knowledge retrieved via cosine similarity search
The `retrieve_knowledge` tool SHALL accept a `query` string, embed it using the same local model, and return the top 5 most similar chunks from the `chunks` table ordered by cosine distance (`<=>` operator).

#### Scenario: Relevant chunks returned for query
- **WHEN** agent calls `retrieve_knowledge(query="LangGraph 的 StateGraph 怎麼用")`
- **THEN** returned chunks contain content semantically related to LangGraph and StateGraph

#### Scenario: Empty result for unrelated query
- **WHEN** agent calls `retrieve_knowledge(query="火星殖民地")` and no related content exists
- **THEN** the tool returns an empty list, not an error

### Requirement: Retrieved chunks injected into agent context
Retrieved chunk contents SHALL be prepended to the LLM's context as a `SystemMessage` before the agent generates a response, clearly labelled as reference material.

#### Scenario: Chunks appear in LLM context
- **WHEN** `retrieve_knowledge` returns results
- **THEN** the agent's next LLM call includes the chunk contents in the system context with a label such as "以下為參考資料："

### Requirement: Related articles recommended alongside answers
When the router classifies intent as `knowledge_query`, the system SHALL return up to 3 related article titles and their source document names alongside the answer.

#### Scenario: Related articles returned with answer
- **WHEN** a knowledge query is answered using retrieved chunks
- **THEN** the response includes a `related_articles` field listing up to 3 article titles from the same or similar documents
