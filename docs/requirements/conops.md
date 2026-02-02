# Concept of Operations (CONOPS)

## 1. Purpose

This Concept of Operations (CONOPS) describes how the **AI-Native Traceability System** will be used in real workflows. It focuses on day-to-day operations for creators and teams, emphasizing low-friction capture of semantic relationships and temporal history.

---

## 2. Operational Context

Creators produce many artifacts while building systems (code, specs, analyses, decisions, tests). Today, these artifacts may be stored in folders, repos, or wikis, but the **relationships between them** are rarely captured and quickly decay.

This system provides a relationship layer that:
- captures what relates to what
- preserves history of those relationships
- enables traceability queries and impact reasoning
- reduces manual overhead via AI proposals

---

## 3. Roles and Responsibilities

### 3.1 Creator (Primary User)
- Produces artifacts in existing tools (editor, IDE, notebook, docs)
- Reviews AI proposals and accepts/rejects links
- Uses queries to regain context and assess impact

### 3.2 Maintainer (Optional)
- Defines or curates schema defaults (types, relationship types)
- Adjusts system settings (noise thresholds, proposal policies)

### 3.3 AI Assistant (System Role)
- Observes working context signals
- Proposes artifact typing and relationships with evidence
- Surfaces orphans and inconsistencies
- Never promotes authoritative links without acceptance

### 3.4 Consumer (Secondary)
- A new team member, reviewer, or downstream agent
- Uses the graph to understand system structure and rationale

---

## 4. Operating Concept

### 4.1 Core Concept

- Artifacts may live anywhere.
- The system maintains a **semantic relationship graph** over artifacts.
- The graph evolves via **events**, enabling history, rewind, and diff.
- AI reduces friction by proposing links and structure.

---

## 5. Typical Usage Scenarios

### Scenario A — New Feature Work

**Goal:** keep requirements/spec/code/test relationships coherent during rapid iteration.

1. Creator begins work; creates or edits artifacts (code, notes, spec fragments).
2. System registers new/updated artifacts.
3. AI proposes:
   - artifact types (e.g., this doc looks like a requirement)
   - links (e.g., this module implements this requirement)
4. Creator accepts/rejects proposals.
5. Creator runs `impact()` before major edits.
6. System maintains history for later review.

**Outcome:** relationships accrue as a side effect of work; traceability exists without a separate clerical task.

---

### Scenario B — Context Re-entry After Time Gap

**Goal:** recover understanding and rationale quickly.

1. Creator returns after weeks/months.
2. Runs `trace()` on a module or requirement.
3. Reviews linked decisions and analyses.
4. Uses `history()` to see what changed and why.

**Outcome:** project memory is externalized; less archaeology.

---

### Scenario C — Review and Change Impact

**Goal:** avoid unintended downstream breakage.

1. Reviewer inspects a proposed change.
2. Runs `impact()` to identify affected requirements/tests/decisions.
3. Checks coverage and orphans.
4. Requests missing links or rejects risky proposals.

**Outcome:** reviews focus on semantics, not file browsing.

---

### Scenario D — AI-Assisted Link Cleanup

**Goal:** improve coherence without manual graph gardening.

1. AI scans for:
   - orphan requirements (no implementing module)
   - orphan tests (verify nothing)
   - weak `relates_to` links that could be upgraded
2. AI proposes candidate edges with evidence.
3. Creator batch-accepts/rejects.

**Outcome:** maintenance is guided and low-effort.

---

## 6. Inputs, Outputs, and Interfaces

### 6.1 Inputs
- Artifact sources: files, repos, wikis, notes
- Context signals: edit events, co-change sets, semantic similarity, references

### 6.2 Outputs
- Relationship graph (authoritative + proposed)
- Event history
- Query results (trace/impact/coverage/history)

### 6.3 Interfaces
- MCP tools (primary programmatic interface)
- Optional UI for browsing graph and timeline

---

## 7. Operational Policies

### 7.1 Authority Policy
- AI output is always **proposed** until accepted.

### 7.2 Evidence Policy
- Every proposed relationship must carry minimal evidence:
  - snippet pointer, file/URI reference, or co-change evidence

### 7.3 Noise Control
- Default behavior should prefer **fewer, higher-quality proposals**.

---

## 8. Deployment Concept

- Local-first installation
- Event log stored locally
- Graph projection stored locally
- Optional export/sync of:
  - relationship map
  - event log snapshots
  - curated graph state

---

## 9. Success Criteria

The system is operationally successful if creators can:
- regain context after time gaps via queries
- see impact of changes without manual archaeology
- maintain relationships with low friction
- avoid drift by surfacing gaps early

---

## 10. Operational Risks

- Proposal overload leading to rejection fatigue
- Schema overreach leading to friction
- Trust erosion if evidence is weak

Mitigations:
- strict separation of proposed vs authoritative
- evidence-first proposals
- minimal schema defaults

---

*This CONOPS defines how the system is used in practice. Architecture documents will formalize system boundaries, interfaces, and flows to implement these operations.*

