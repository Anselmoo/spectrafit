# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for SpectraFit. ADRs document significant architectural decisions made during the development of the project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help:

- Document the reasoning behind key decisions
- Provide historical context for future maintainers
- Create a knowledge base of architectural patterns
- Support onboarding of new team members

## ADR Format

Each ADR follows this structure:

1. **Status**: Proposed, Accepted, Deprecated, Superseded
2. **Context**: The issue motivating this decision
3. **Decision**: The change being proposed or made
4. **Consequences**: The resulting context after applying the decision

## Index

### ADR-001: Typer CLI Migration

**Status**: Accepted (v1.4.0+)

Migration from `argparse` to Typer for improved CLI experience, type safety, and testing capabilities.

[Read ADR-001 →](./ADR-001-typer-cli-migration.md)

### ADR-002: Plugin Architecture

**Status**: Accepted (v2.0.0)

Implementation of a formal plugin system using protocols, entry points, and a discovery mechanism for extensibility.

[Read ADR-002 →](./ADR-002-plugin-architecture.md)

### ADR-003: Subcommand Structure

**Status**: Accepted (v2.0.0)

Restructuring the CLI into a hierarchical subcommand architecture for better organization and discoverability.

[Read ADR-003 →](./ADR-003-subcommand-structure.md)

## Decision Process

When making architectural decisions:

1. **Identify the need**: Document the problem or opportunity
2. **Research alternatives**: Investigate different solutions
3. **Propose decision**: Create draft ADR with options
4. **Review**: Discuss with team/community
5. **Accept**: Mark status as "Accepted" and implement
6. **Update**: Revise if consequences emerge

## ADR Lifecycle

- **Proposed**: Under discussion, not yet decided
- **Accepted**: Decision made and being implemented
- **Deprecated**: No longer recommended but not yet replaced
- **Superseded**: Replaced by another ADR (link to replacement)

## Creating a New ADR

To create a new ADR:

1. Copy the ADR template (or use an existing ADR as reference)
2. Number it sequentially (ADR-004, ADR-005, etc.)
3. Fill in all sections
4. Submit for review via pull request
5. Update this README with the new ADR

## ADR Template

```markdown
# ADR-XXX: [Title]

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-YYY]

## Context

[Describe the forces at play, including technological, political, social, and project local. These forces are probably in tension, and should be called out as such.]

## Decision

[Describe our response to these forces. This is the "we will" statement.]

## Consequences

### Positive
- ✅ [Benefit 1]
- ✅ [Benefit 2]

### Negative
- ⚠️ [Drawback 1]
- ⚠️ [Drawback 2]

### Neutral
- 📝 [Neutral consequence 1]

## Alternatives Considered

### Alternative 1
**Pros**: ...
**Cons**: ...

## Related Decisions

- ADR-XXX: [Related decision]

## References

- [Link to relevant documentation]

## Revision History

| Date | Version | Author | Description |
|------|---------|--------|-------------|
| YYYY-MM-DD | 1.0 | Name | Initial version |
```

## References

- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [Architectural Decision Records](https://github.com/joelparkerhenderson/architecture-decision-record)

## Contributing

We welcome contributions to our ADRs! Please:

1. Follow the ADR template
2. Be clear and concise
3. Include context and reasoning
4. Document alternatives considered
5. Update this index when adding new ADRs
