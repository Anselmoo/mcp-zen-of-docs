# Architecture

## Components

Use the [C4 model](https://c4model.com/) levels to structure this section:

### System context

- Describe how this system fits into the broader ecosystem and its external dependencies.

### Container diagram

- List the major deployable units (services, databases, message queues).
- State the technology choice and runtime for each container.

### Component responsibilities

| Component | Owner | Responsibility | Key interfaces |
| --------- | ----- | -------------- | -------------- |
| *Name*    | *Team/person* | *One-sentence purpose* | *APIs, events, files* |

- Document ownership and on-call responsibilities for each component.
- Link to relevant [Architecture Decision Records](#decision-log) for design rationale.

## Decision log

Record architectural decisions using the ADR (Architecture Decision Record) format:

### Template

- **ADR-NNN: Title** (YYYY-MM-DD)
- **Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
- **Context:** What is the issue or problem that motivates this decision?
- **Decision:** What is the change that is being proposed or adopted?
- **Consequences:** What are the tradeoffs and implications of this decision?

Keep the decision log in reverse-chronological order (newest first).

## Related docs

- [Documentation home](./index.md)
- [Table of contents](./toc.md)
- [API reference](./api.md)
