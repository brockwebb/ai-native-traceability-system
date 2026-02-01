# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Native Traceability System — project memory infrastructure that survives context windows, thread death, and human absence. Captures relationships between artifacts (requirements, code, tests, decisions) as you work, not after.

**Current status:** Design/specification phase. Design docs in `docs/`. No source code implemented yet.

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

1. **Minimal Core** — Event log, NetworkX projection, minimal schema, manual artifact registration, query tools
2. **AI Proposals** — Proposal generation, accept/reject workflow, evidence + confidence
3. **Temporal Features** — Rewind, diff, history queries
4. **Parsers** — Automatic anchor extraction (Markdown headings, Python AST)
5. **Claude Code Integration** — Skills for capture during work
