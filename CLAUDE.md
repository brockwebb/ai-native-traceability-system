# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Native Traceability System — project memory infrastructure that survives context windows, thread death, and human absence. Captures relationships between artifacts (requirements, code, tests, decisions) as you work, not after.

**Current status:** Core implementation complete. MCP server operational. System is dogfooding itself (see `.trace/events.jsonl`).

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `docs/` | Design documents, specifications, decision records |
| `handoffs/` | Session handoff notes for context continuity between threads |
| `cc_tasks/` | Claude Code task files — instructions for CC to execute |

**Full paths (always use these to avoid ambiguity):**
- **Handoffs:** `/Users/brock/Documents/GitHub/ai-native-traceability-system/handoffs/`
- **CC Tasks:** `/Users/brock/Documents/GitHub/ai-native-traceability-system/cc_tasks/`

**When writing handoffs:** Save to handoffs directory with date prefix (e.g., `2025-01-31_session_notes.md`)

**When writing CC tasks:** Save to cc_tasks directory with descriptive name (e.g., `implement_event_parser.md`)

## Architecture

Core axiom: *Artifacts are inputs. Relationships are the system.*

### Source of Truth
- **Event log:** `events.jsonl` — append-only, one JSON event per line, lives in repo
- Human-readable, git-diffable, no binary formats

### Graph Projection
- **NetworkX** — Python, in-memory, rebuilt from events on load
- Zero infrastructure dependency
- Neo4j optional for power users, not default

### Authority Model
- AI writes everything as `proposed` — zero friction capture
- Human approves in batches at natural breakpoints
- Both proposed and authoritative states are queryable
- Proposed = working memory, Authoritative = committed memory

### File Structure (planned)
```
.trace/
  events.jsonl      # append-only event log (source of truth)
  anchors.yaml      # external index of in-file locations
```

## Design Documents

All in `docs/`:
- `ai_native_traceability_system_top_level_vision_plan.md` — vision, objectives
- `system_requirements_specification_*.md` — FR-1 through FR-17
- `architecture_specification_*.md` — component diagrams (note: Neo4j replaced by NetworkX)
- `detailed_design_specification_*.md` — data model, services, milestones
- `concept_of_operations_conops_*.md` — usage scenarios
- `analysis_of_alternatives_*.md` — BUILD decision rationale
- `design_decisions_2025-01-31.md` — **current working decisions**, supersedes older docs where they conflict

## Technology Stack

- Python
- NetworkX (in-memory graph projection)
- JSONL (event log format)
- No database server required for core function

## Implementation Milestones

1. ✅ **Minimal Core** — Event log, NetworkX projection, minimal schema, manual artifact registration, query tools
2. ✅ **AI Proposals** — Proposal generation, accept/reject workflow, evidence + confidence
3. **Temporal Features** — Rewind, diff, history queries
4. **Parsers** — Automatic anchor extraction (Markdown headings, Python AST)
5. ✅ **Claude Code Integration** — Skills for capture during work

## Traceability Integration

This repository uses AI-native traceability to track relationships between requirements, code, tests, and decisions.

**Claude Code should:**
1. **Capture new artifacts automatically** - Register files when creating them
2. **Propose links when relationships are clear** - Connect requirements to implementations, tests to code, etc.
3. **Check impact before major changes** - Use `impact()` to see downstream effects
4. **End sessions with approval reminder** - Note how many proposed links await approval

**Skill file:** See `.claude/skills/traceability.md` for detailed patterns and workflows.

**MCP Tools Available:**
- `trace(artifact_id)` - Show upstream/downstream neighbors
- `impact(artifact_id)` - See what breaks if this changes
- `orphans()` - Find unlinked artifacts
- `proposed_links()` - Review pending approvals
- `add_artifact(id, type, file_path)` - Register new artifact
- `propose_link(source, target, rel_type, rationale)` - Create relationship
- `accept_proposal(source, target)` - Promote to authoritative (human only)

**Current trace state:**
- View: `.trace/events.jsonl` (append-only event log)
- Query: `python scripts/query_trace.py`
- Regenerate: `python scripts/dogfood_trace.py`

## MCP Configuration (Project-Scoped)

This project uses **project-scoped MCP configuration** via `.mcp.json` in the project root.

**IMPORTANT:** Only the `trace:*` tools are available in this project context.

### Available Tools (10 total)

**Read-Only Queries:**
1. `trace(artifact_id)` - Get upstream/downstream neighbors
2. `impact(artifact_id)` - See all affected artifacts
3. `orphans()` - Find unlinked artifacts
4. `decisions()` - Get all decision records
5. `proposed_links()` - List pending approvals

**Discovery Tools:**
6. `list_artifacts(artifact_type?)` - List all artifacts
7. `search_artifacts(query?, type?, tags?)` - Search artifacts

**Write Operations:**
8. `add_artifact(id, type, file_path?, tags?)` - Register artifact
9. `propose_link(source, target, rel_type, rationale)` - Create link
10. `accept_proposal(source, target)` - Promote to authoritative

### What's NOT Available

**No database servers in this project:**
- ❌ No Neo4j tools (this project uses NetworkX, not Neo4j)
- ❌ No PostgreSQL tools (no database server)
- ❌ No arnold-* tools (different project)
- ❌ No census-* tools (different project)

**This project uses:**
- ✅ NetworkX (in-memory graph)
- ✅ JSONL files (`.trace/events.jsonl`)
- ✅ Zero infrastructure dependencies
- ✅ Git-integrated storage

### Configuration File

**Location:** `.mcp.json` (project root)

```json
{
  "mcpServers": {
    "trace": {
      "command": "/opt/anaconda3/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/brock/Documents/GitHub/ai-native-traceability-system",
      "env": {
        "TRACE_DIR": "/Users/brock/Documents/GitHub/ai-native-traceability-system/.trace"
      }
    }
  }
}
```

**Key Points:**
- Uses explicit Python path (not `trace-mcp` command)
- Project-scoped: Only applies when working in this repository
- Single server: Only `trace` server, no other MCP servers
- File-based: All data in `.trace/events.jsonl`
