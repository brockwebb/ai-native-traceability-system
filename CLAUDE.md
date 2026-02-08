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

**When referencing files in conversation:** Always use full absolute paths when handing off a file path to the user. This eliminates ambiguity and reduces token waste from clarification. Example: "Task ready: `/Users/brock/Documents/GitHub/ai-native-traceability-system/cc_tasks/2025-02-03_req_init_001.md`"

## Architecture

Core axiom: *Artifacts are inputs. Relationships are the system.*

### Source of Truth
- **Event log:** `events.jsonl` — append-only, one JSON event per line, lives in repo
- Human-readable, git-diffable, no binary formats

### Graph Projection
- **NetworkX** — Python, in-memory, rebuilt from events on load
- Zero infrastructure dependency
- Neo4j optional for power users, not default

### Authority Model: DD-AUTO-ACCEPT-001 (SUPERSEDES ALL PRIOR)

The system documents itself confidently. Auto-accept is the default.

**DO NOT** propose batch approval workflows, human review gates, or
"proposed → human approves" patterns. This was explicitly superseded.

| Situation | Behavior |
|-----------|----------|
| Routine capture | Auto-accept. Silent. Confident. |
| High-impact change (breaks existing links) | Warn, human decides, decision traced |
| Human reviewing reports/RTMs | Corrections made explicitly |
| Ambiguous/unclear | Ask, human provides direction |

The spider spins its web. Human corrects after the fact, not before.

### File Structure (planned)
```
.trace/
  events.jsonl      # append-only event log (source of truth)
  anchors.yaml      # external index of in-file locations
```

## Design Documents

Organized by systems engineering template:
- `docs/requirements/vision.md` — vision, objectives
- `docs/requirements/srs.md` — FR-1 through FR-17
- `docs/requirements/conops.md` — usage scenarios
- `docs/architecture/system_architecture.md` — component diagrams (note: Neo4j replaced by NetworkX)
- `docs/design/detailed_design.md` — data model, services, milestones
- `docs/decisions/design_decisions.md` — **current working decisions**, supersedes older docs where they conflict
- `docs/decisions/analysis_of_alternatives.md` — BUILD decision rationale
- `docs/decisions/dd_methodology_templates.md` — methodology template design

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
2. **Auto-accept links when relationships are clear** - Connect requirements to implementations, tests to code, etc. (routine capture is auto-accepted)
3. **Check impact before major changes** - Use `impact()` to see downstream effects, warn on high-impact changes

**Skill file:** See `.claude/skills/traceability.md` for detailed patterns and workflows.

**MCP Tools Available:**
- `trace(artifact_id)` - Show upstream/downstream neighbors
- `impact(artifact_id)` - See what breaks if this changes
- `orphans()` - Find unlinked artifacts
- `proposed_links()` - Review links (mostly for debugging, auto-accept is default)
- `add_artifact(id, type, file_path)` - Register new artifact
- `propose_link(source, target, rel_type, rationale)` - Create relationship (auto-accepted)
- `accept_proposal(source, target)` - Explicit accept (for corrections/high-impact)

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
9. `propose_link(source, target, rel_type, rationale)` - Create link (auto-accepted for routine capture)
10. `accept_proposal(source, target)` - Explicit promotion (for corrections/high-impact changes)

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
