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

## 10. Implementation Plan (Milestones)

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

## 11. Design Risks

- Proposal noise overwhelms creators
- Schema rigidity recreates legacy friction
- Inference quality causes mistrust

Mitigations:
- strong defaults + minimal schema
- separation of proposed vs authoritative
- evidence-first proposals

---

*This DDS defines the minimum viable architecture and the path to a usable system that preserves semantic traceability over time.*

