# Analysis of Alternatives (AoA)

## 1. Purpose

The purpose of this AoA is to determine whether an existing product or open‑source system satisfies the need for an **AI‑native, low‑friction traceability system** that captures files, artifacts, and their relationships *as work happens*, or whether a custom build is warranted.

This AoA is intentionally narrow: the question is **build vs adopt**, not feature comparison across traditional tools.

---

## 2. Problem Restatement

Modern projects suffer from rapid **context drift**:
- Relationships between requirements, code, decisions, tests, and analyses are not captured
- Documentation exists, but semantics ("what relates to what, and why") do not
- AI accelerates artifact creation but amplifies disorganization
- Existing tools require humans to do the cognitive bookkeeping

The desired capability is **traceability that emerges as a side‑effect of working**, with AI absorbing the overhead of tagging, linking, and surfacing relationships.

---

## 3. Evaluation Criteria

Alternatives were evaluated against the following non‑negotiable criteria:

1. **Relationship‑First** – Explicit, typed relationships are first‑class
2. **AI‑First Design** – AI is structural, not bolted on
3. **Low Human Overhead** – Humans are not primary link maintainers
4. **Temporal History** – Change over time is preserved and queryable
5. **Engineer‑First Value** – Immediate benefit to builders, not auditors
6. **Tool‑Agnostic** – Artifacts may live anywhere (files, wikis, repos)

---

## 4. Alternatives Considered

### 4.1 Documentation‑Centric Tools
**Examples:** Confluence, Notion, MkDocs, GitHub Wikis

- Strengths: storage, publishing, collaboration
- Limitations:
  - Relationships are manual hyperlinks
  - No semantic graph
  - No temporal intent tracking

**Result:** ❌ Does not meet criteria

---

### 4.2 Code Intelligence & Repo Analysis Tools
**Examples:** Sourcegraph, code visualization tools

- Strengths: understands code structure
- Limitations:
  - No requirements or decision modeling
  - No rationale capture
  - No documentation semantics

**Result:** ❌ Partial, insufficient

---

### 4.3 Graph‑Based Note Systems
**Examples:** Obsidian, Logseq, Dendron

- Strengths: bidirectional links, graph views
- Limitations:
  - Manual linking dominates
  - No AI‑maintained semantics
  - No first‑class temporal model

**Result:** ❌ Human overhead too high

---

### 4.4 Enterprise Service Catalogs
**Examples:** Backstage (Spotify)

- Strengths: service relationships, ownership models
- Limitations:
  - Heavyweight
  - Infrastructure‑centric
  - Not AI‑first

**Result:** ❌ Misaligned

---

### 4.5 Requirements Management Systems
**Examples:** DOORS, ReqView, Doorstop

- Strengths:
  - Traceability conceptually correct
  - Explicit linkage models
- Limitations:
  - High friction
  - Compliance‑first
  - Manual maintenance
  - Not AI‑native

**Result:** ❌ Correct idea, wrong execution

---

### 4.6 Versioned / Temporal Knowledge Graphs
**Examples:** TerminusDB, Datahike, Graphiti

- Strengths:
  - Temporal history
  - Graph semantics
- Limitations:
  - No requirements‑specific schema
  - No end‑to‑end workflow
  - No engineer‑first UX

**Result:** ⚠ Building blocks only

---

## 5. Findings

- No existing product provides **end‑to‑end AI‑native traceability** across artifacts
- Existing tools either:
  - store artifacts without semantics, or
  - model semantics with prohibitive human overhead
- AI is universally treated as an assistant, not as **infrastructure**

The desired capability does **not exist as a cohesive system**.

---

## 6. Decision

**Decision:** BUILD

Rationale:
- The gap is architectural, not incremental
- Retrofitting legacy tools would recreate existing failure modes
- Core requirements demand AI‑first assumptions
- Building allows explicit control over schema, semantics, and evolution

---

## 7. Implications

- Scope must be tightly controlled to avoid recreating DOORS‑style friction
- Initial implementation should prioritize:
  - minimal schema
  - explicit relationships
  - event‑sourced history

---

## 8. Next Artifacts

- System Requirements Specification
- Verification & Validation (V&V) Matrix
- Detailed Design Specification
- Architecture Diagrams
- CONOPS

---

*Conclusion: This is a justified build decision based on demonstrated market absence and architectural mismatch.*

