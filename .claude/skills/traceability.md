# Traceability Skill

This skill enables capture of traceability relationships during work.

## When to Capture

- **Decisions**: When we make a choice between alternatives, log it
- **Implementations**: When code implements a requirement, link them
- **Dependencies**: When one artifact depends on another, link them
- **Tests**: When a test verifies a requirement, link them

## Capture Commands

Use MCP tools to capture relationships:

- `trace(artifact_id)` - See what's connected to an artifact
- `impact(artifact_id)` - See what breaks if this changes
- `propose_link(source, target, type, rationale)` - Propose a relationship
- `decisions()` - Review logged decisions

## Authority Model

- AI writes everything as **proposed**
- Human reviews and approves in batches
- Both proposed and authoritative are queryable

## Best Practices

1. Capture during work, not after
2. Include rationale with every link
3. Use specific relationship types (implements, depends_on, verifies)
4. Keep artifact IDs stable and meaningful
