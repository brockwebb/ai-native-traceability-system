# Design Decisions — AI-Native Traceability System

**Date:** 2025-01-31  
**Status:** Working document — captures decisions diverging from initial design docs

---

## 1. Problem Reframe

The original documentation frames this as a formal traceability system (modern DOORS). The actual problem is more immediate:

**Primary problem:** Claude's context limits create constant overhead. Every new thread starts near-zero. Every long thread drifts. The human becomes RAM, reloading context repeatedly.

**Secondary problem:** Human amnesia after time gaps. Returning to a project after weeks or months requires archaeology to recover decisions, rationale, and artifact locations.

**The system is project memory infrastructure that survives context windows, thread death, and human absence.**

---

## 2. Core Requirements

### 2.1 Baseline (shared with existing context managers)

- **Persist across sessions** — memory survives thread death
- **MCP interface** — Claude can query and write via tools
- **Survive compaction** — context limits don't destroy project knowledge

### 2.2 Differentiators (what existing tools don't do)

- **Typed relationships** — `implements`, `depends_on`, `verifies`, `supersedes` — not just blobs of text
- **Impact queries** — "what breaks if X changes?" answerable from the graph
- **Artifact anchors with drift detection** — know *where* in a file something lives, detect when it moves
- **Decision-first** — not just "what happened" but "what we decided and why"
- **Proposed vs authoritative state** — AI writes freely, human approves in batches

### 2.3 Operational Requirements

1. **Claude can query it** — MCP tools answer "where is X," "what did we decide about Y," "what depends on Z"
2. **Capture happens during work** — not a separate documentation phase
3. **Break-fix history** — "we tried X, it broke Y, we reverted" is queryable
4. **Survives thread death** — graph persists, any Claude instance reconnects via queries
5. **Impact cascades** — "requirement X changed, what's affected?"

---

## 3. Authority Model

**Constraint:** AI writing freely without approval has caused costly mistakes requiring days to untangle.

**Decision:** 

- AI writes everything as `proposed` — zero friction capture
- Both proposed and authoritative states are queryable
- Approval happens in batches at natural breakpoints (end of session, before commits)
- High-risk operations flagged for immediate review
- Proposed is working memory, authoritative is committed memory

---

## 4. Architecture

### 4.1 Source of Truth

**Event log:** `events.jsonl` — append-only, one JSON event per line, lives in repo.

- Human-readable
- Git-diffable
- Language-agnostic
- No binary formats, no pickle, no database files

### 4.2 Graph Projection

**NetworkX** — Python, in-memory, rebuilt from events on load.

- Pure Python, `pip install`, no server
- Works identically in Claude Code and Claude Desktop
- No infrastructure dependency
- No connection management

**Why not Neo4j as default:**
- Heavy infrastructure requirement
- Not portable across environments
- Couples the system to specific tooling

Neo4j remains optional for power users who want persistent graph queries.

### 4.3 File Structure

```
.trace/
  events.jsonl      # append-only event log (source of truth)
  anchors.yaml      # external index of in-file locations
```

Minimal clutter. One directory, two files.

---

## 5. Traceability Granularity

### 5.1 No In-File Markers

Location metadata lives in the graph, not in source files.

**Why:**
- Developers delete "magic comments"
- Some file types don't support comments (JSON, images, binaries)
- Markers drift when code moves
- External index is decoupled and verifiable

### 5.2 Anchor Structure

```yaml
# .trace/anchors.yaml
REQ-FR-005:
  file: docs/requirements.md
  section: "4.3.1"
  heading: "Authentication Requirements"
  line_start: 45
  line_end: 67
  content_hash: "a7f3b2c..."
```

### 5.3 Granularity Levels

| Level | Use case |
|-------|----------|
| File | Default for most artifacts |
| Section/heading | Requirements docs, specs, key decisions |
| Function/class | Critical code paths, entry points |
| Line | Avoid — churn makes it unmaintainable |

### 5.4 Drift Detection

- Hash the referenced content section on registration
- On load, re-parse and compare hash
- Mismatch → flag stale: "REQ-FR-005 content changed, verify dependencies"
- Query affected components for cascade review

---

## 6. Parsers

Automatic anchor extraction per file type:

| File type | Anchor extraction |
|-----------|-------------------|
| Markdown | Headings, numbered sections |
| Python | AST — functions, classes |
| YAML/JSON | Top-level keys (file-level for nested) |
| Binaries | File-level only |

Parsers extract anchors automatically. No manual tagging required for standard structures.

---

## 7. Interface

**Primary:** Claude Code tasks and skills

- Capture during work
- Common patterns as commands ("log decision," "link artifact," "what depends on X")
- MCP tools for queries from any Claude instance

**Secondary:** Direct Python scripts for non-Claude workflows

---

## 8. Event Schema (Draft)

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "event_type": "ARTIFACT_ADDED | DECISION_LOGGED | LINK_ADDED | LINK_PROMOTED | ANCHOR_STALE | ...",
  "actor": "human | ai:claude-code | ai:claude-desktop",
  "state": "proposed | authoritative",
  "payload": { ... },
  "rationale": "optional short text"
}
```

---

## 9. Query Examples

```
trace(artifact_id)     → upstream/downstream neighbors
impact(artifact_id)    → what's affected if this changes
orphans()              → artifacts missing required relationships
history(artifact_id)   → event history, state over time
stale()                → anchors with content hash mismatch
decisions(date_range)  → decisions logged in period
```

---

## 10. Open Questions

- Exact properties per artifact type (requirement, decision, module, test, etc.)
- Parser implementation details
- Batch approval UX — what does "end of session" look like?
- How to handle multi-file artifacts (e.g., a module spanning several files)

---

## 11. Relationship to Original Documents

This document captures decisions that diverge from or refine the initial design docs:

- `docs/requirements/vision.md` — vision still valid
- `docs/requirements/srs.md` — FR-1 through FR-17 still valid, reframed around memory problem
- `docs/architecture/system_architecture.md` — Neo4j assumption replaced with NetworkX
- `docs/design/detailed_design.md` — authority model refined, file structure simplified
- `docs/requirements/conops.md` — Claude Code as primary interface added

Original documents reorganized into SE template structure.

---

*This document will evolve as implementation proceeds.*
