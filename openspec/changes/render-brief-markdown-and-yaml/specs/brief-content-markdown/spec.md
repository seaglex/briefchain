## ADDED Requirements

### Requirement: Brief content is rendered as Markdown
The system SHALL render `brief.content` as Markdown in the brief detail page content area.

#### Scenario: View brief with Markdown content
- **WHEN** a user opens a brief whose content contains Markdown syntax
- **THEN** the detail page renders headings, lists, bold, italic, links, and paragraphs according to Markdown rules

### Requirement: Plain text fallback is preserved
The system SHALL render content that contains no Markdown syntax as normal paragraphs.

#### Scenario: View brief with plain text content
- **WHEN** a user opens a brief whose content has no Markdown syntax
- **THEN** the content is displayed as plain paragraphs without visible parsing artifacts
