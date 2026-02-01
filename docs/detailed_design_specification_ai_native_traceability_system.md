# Detailed Design Specification (DDS)

## 1. Purpose

This Detailed Design Specification defines the architecture, data model, core services, and interaction patterns for the **AI-Native Traceability System**. It is derived from the Vision, AoA (BUILD decision), SRS, and V&V Matrix.

Design goal: deliver **semantic traceability with minimal friction**, where AI assists but does not become the authority.

---

## 2. Design Principles

1. **Graph is the product**: the relationship graph is the primary output.
2. **Local-first**: works offline, sync is optional.
3. **Event-sourced**: all state is replayable from an immutable log.
4. **AI proposes, humans approve**: AI never silently promotes authoritative links.
5. **Explicit beats inferred**: inferred relationships are proposals until accepted.
6. **Tool-agnostic artifacts**: artifacts can live anywhere; storage substrate is not the system.

---

## 3. System Architecture Overview

### 3.1 Logical Components

1. **Artifact Registry**
   - Registers and normalizes artifacts from various substrates
   - Assigns stable identifiers

2. **Schema & Typing Layer**
   - Defines artifact types and relationship types
   - Extensible without disruptive migration

3. **Event Log (Source of Truth)**
   - Append-only log of graph mutations
   - Durable and replayable

4. **Graph Projection Store**
   - Materialized graph for querying (projection)
   - Rebuildable from event log

5. **AI Assistance Service**
   - Generates proposals: candidate nodes/edges, missing links, inconsistencies
   - Produces evidence/rationale with each proposal

6. **Query Interface (MCP Layer)**
   - Tool calls that return trace/impact/coverage/history
   - Read-first; write operations are controlled and explicit

7. **UI / Visualization (Optional)**
   - Graph explorer and timeline replay
   - Not required for core value

---

## 4. Data Model

### 4.1 Identifiers

- Every entity uses a stable, unique ID.
- IDs may be either:
  - **Human-assigned** (preferred for long-lived objects)
  - **System-assigned** (for ephemeral artifacts)

Recommended ID pattern (illustrative):
- `ART-000123` (generic artifact)
- `REQ-0012`, `DEC-0007`, `MOD-auth-001`, `TEST-0045`

### 4.2 Core Node Types

Minimum viable set:

- **Artifact** (base type)
  - `id`, `type`, `title`, `uri`, `created_at`, `updated_at`, `source`

Specializations (via `type` or labels):
- `requirement`
- `decision`
- `module`
- `test`
- `analysis`
- `spec`
- `issue`
- `prompt` (optional)

### 4.3 Relationship Types

Minimum viable set:

- `implements` (module → requirement)
- `verifies` (test → requirement)
- `depends_on` (artifact → artifact)
- `specifies` (spec/doc → module/requirement)
- `justifies` (decision → requirement)
- `relates_to` (weak link; use sparingly)

Relationship properties:
- `state`: `proposed` | `authoritative`
- `proposed_by`: `ai` | `human`
- `evidence`: short text/snippet pointers
- `confidence`: 0–1 (for proposed)
- `created_at`, `accepted_at` (if authoritative)

---

## 5. Event Model

### 5.1 Event Types

All mutations are recorded as events:

- `NODE_ADDED`
- `NODE_UPDATED`
- `NODE_REMOVED`
- `EDGE_ADDED`
- `EDGE_UPDATED`
- `EDGE_REMOVED`
- `PROPOSAL_ACCEPTED`
- `PROPOSAL_REJECTED`

### 5.2 Event Envelope

Each event includes:
- `event_id`
- `timestamp`
- `actor` (human identifier or `ai:<agent>`)
- `event_type`
- `payload` (node/edge mutation)
- `correlation_id` (groups events from one operation)
- `rationale` (optional, short)

### 5.3 Rewind and Diff

- **Rewind**: replay events up to time T into a projection
- **Diff**: compute differences between projections at T1 and T2

---

## 6. Service Responsibilities

### 6.1 Artifact Registry

Inputs:
- filesystem paths
- repo URIs
- wiki/page URIs

Outputs:
- normalized Artifact nodes

Key functions:
- canonicalization (path/URI normalization)
- stable ID mapping

### 6.2 AI Assistance Service

Produces:
- proposed edges with evidence
- suggested artifact typing
- orphan and inconsistency reports

Constraints:
- never writes authoritative edges directly
- all proposals are explicit and reviewable

### 6.3 Graph Projection Store

- Maintains current authoritative graph view
- Also stores proposed edges (separate state)
- Can be rebuilt from event log deterministically

Storage options:
- Neo4j (graph store)
- Alternative: other graph DB + event replay

---

## 7. MCP Tool Interface

### 7.1 Read Tools (Minimum)

- `trace(artifact_id)`
  - returns upstream/downstream neighbors by relationship type

- `impact(artifact_id | uri)`
  - returns requirements/tests/decisions affected by a change

- `orphans()`
  - returns artifacts missing required relationships

- `history(artifact_id, t1?, t2?)`
  - returns event history and state diffs

- `coverage()`
  - computes implementation and verification coverage over requirements

### 7.2 Write Tools (Controlled)

- `propose_links(context)`
- `accept_proposal(proposal_id)`
- `reject_proposal(proposal_id)`

Write tools shall:
- require explicit user invocation
- create events for acceptance/rejection

---

## 8. System and Data Flow Diagrams

### 8.1 System Flow (Textual)

1. Creator edits artifacts in any tool
2. Artifact Registry detects/ingests artifacts
3. AI Assistance generates proposals (edges, types)
4. Creator reviews and accepts/rejects proposals
5. Acceptance emits events to Event Log
6. Projection updates queryable graph state
7. MCP tools serve queries to humans/agents

### 8.2 Data Flow (Textual)

- Artifacts → Registry → Node events
- Context signals → AI Assist → Proposal events
- Proposal decisions → Acceptance events
- Event Log → Projection rebuild → Query graph

---

## 9. Security & Trust Boundaries

- AI output is untrusted until accepted
- Proposal evidence must reference real artifacts/locations
- Optional role-based controls for acceptance in team settings

---

## 10. Design Decisions Rationale

### Why events.jsonl + NetworkX over Neo4j

**Problem constraint:** The system must work identically across Claude Code, Claude Desktop, and standalone scripts without infrastructure setup.

**Neo4j costs:**
- Requires running server process
- Connection management overhead
- Not portable across environments without Docker or install
- Overkill for single-project, single-user memory

**JSONL + NetworkX benefits:**
- Zero infrastructure — `pip install networkx`, done
- Event log is human-readable, git-diffable, inspectable when things break
- Graph rebuilds from events in milliseconds for typical project size
- Same code runs everywhere Python runs
- Source of truth is plain text, not a database

**Trade-off accepted:** This prioritizes portability and correctness over query performance at scale. For personal/team project memory (hundreds to low thousands of artifacts), this is the right trade. If someone needs 50K+ nodes with complex traversals, Neo4j remains available as optional projection target.

### Why external anchors over in-file markers

**In-file markers fail because:**
- Developers delete "magic comments" during cleanup
- Some file types don't support comments (JSON, binaries)
- Markers drift silently when code moves
- Creates coupling between tool and source files

**External anchors succeed because:**
- Decoupled from source — files stay clean
- Hash-based verification detects drift explicitly
- Works uniformly across all file types
- Location metadata is queryable, not hidden in comments

### Why proposed/authoritative over immediate writes

**Learned from failure:** Unconstrained AI writes caused costly mistakes requiring days to untangle. The "vibe coding" failure mode is real.

**But per-item approval kills adoption:** Constant interruption makes the tool annoying, then abandoned.

**Batch approval at breakpoints:** Captures the benefit of human authority without the friction. Proposed state is immediately useful for queries — it's working memory, not limbo.

---

## 11. Open Questions

- *Caution: Keep artifact types descriptive, not normative. Let relationships carry most of the meaning. Prefer adding properties later over enforcing schemas early.*

---

## 12. Implementation Plan (Milestones)

### Milestone 1 — Minimal Core
- Event log + projection
- minimal schema
- manual artifact registration
- MCP read tools: trace/impact/orphans

### Milestone 2 — AI Proposals
- proposal generation
- acceptance/rejection workflow
- evidence + confidence capture

### Milestone 3 — Temporal Features
- rewind
- diff
- history queries

### Milestone 4 — Packaging
- containerized stack
- local-first defaults
- optional git sync/export

### Milestone 5 — Visualization (Optional)
- timeline playback
- graph evolution animation

---

## 13. Design Risks

- Proposal noise overwhelms creators
- Schema rigidity recreates legacy friction
- Inference quality causes mistrust

Mitigations:
- strong defaults + minimal schema
- separation of proposed vs authoritative
- evidence-first proposals

---

*This DDS defines the minimum viable architecture and the path to a usable system that preserves semantic traceability over time.*

