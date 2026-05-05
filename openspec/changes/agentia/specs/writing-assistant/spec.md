## ADDED Requirements

### Requirement: Draft new post in author's writing style
When intent is `writing_assist` and user requests a draft, the system SHALL retrieve a sample of the author's existing blog posts from the knowledge base, use them as style reference, and generate a draft in the same tone, structure, and vocabulary.

#### Scenario: Draft generated with style reference
- **WHEN** user requests "幫我寫一篇關於 pgvector 的文章"
- **THEN** agent retrieves 3–5 existing posts as style examples and produces a draft that matches the author's writing style

### Requirement: Tag suggestions generated from draft content
After generating a draft, the system SHALL analyse the content and suggest 3–5 relevant tags drawn from tags already used in existing blog posts.

#### Scenario: Tags suggested after draft
- **WHEN** a draft is generated
- **THEN** the response includes a `suggested_tags` list of 3–5 strings matching existing tag vocabulary

### Requirement: Cross-reference candidates identified
When generating a draft or on explicit request, the system SHALL search the knowledge base for existing posts that are topically related and return up to 5 candidates that the author may want to link to.

#### Scenario: Cross-reference candidates returned
- **WHEN** a draft about RAG is generated
- **THEN** the response includes a `cross_references` list of up to 5 existing post titles related to RAG, embeddings, or search

### Requirement: Author can refine draft through conversation
The writing assistant SHALL maintain the draft in conversation state across turns, allowing the author to request revisions ("讓第二段更簡潔") without starting over.

#### Scenario: Revision applied to existing draft
- **WHEN** author sends a follow-up refinement request after a draft was generated
- **THEN** the revised draft reflects the requested change while preserving unchanged sections
