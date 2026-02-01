# AI-Native Traceability System

Project memory infrastructure for AI-assisted development. Captures relationships between artifacts (requirements, code, tests, decisions) as you work — survives context windows, thread death, and human absence.

## Problem

LLM context limits create constant overhead. Every new thread starts near-zero. Every long thread drifts. You become RAM, reloading Claude with "remember, the architecture is HERE, the decision about X was THIS."

Same problem after time gaps — returning to a project after weeks means archaeology to recover what exists and why.

## Solution

A lightweight traceability graph that lives in your repo:
- **Decisions captured as they happen**, not in a separate documentation phase
- **Impact queries**: "what depends on this requirement?"
- **Artifact registry**: "where is the auth module?"
- **Break-fix history**: "we tried X, it broke Y, we reverted"

Claude queries the graph via MCP tools. Context survives thread death.

## How It Works

```
.trace/
  events.jsonl      # append-only event log (source of truth)
  anchors.yaml      # maps artifacts to file locations
```

- **Event log** is human-readable, git-diffable, no database required
- **Graph** rebuilt in-memory (NetworkX) from events on load
- **AI writes proposed**, human approves in batches — no unchecked writes

## Installation

```bash
pip install ai-native-trace
```

Add to your Claude MCP config, then in your project's `CLAUDE.md`:

```markdown
Use traceability tools to log decisions and query impact before major changes.
```

## Usage

Talk to Claude:
- "Log decision: we're using NetworkX instead of Neo4j because..."
- "What depends on the authentication module?"
- "What decisions have we made this week?"
- "Show me orphan requirements with no implementation"

The MCP server handles the rest.

## Status

**Design phase.** Core implementation in progress. This repo dogfoods itself — the `.trace/` directory tracks this project's own evolution.

## Documentation

See `docs/` for design specifications:
- `design_decisions_2025-01-31.md` — current working decisions
- `system_requirements_specification_*.md` — functional requirements
- `architecture_specification_*.md` — system architecture

## License

MIT
