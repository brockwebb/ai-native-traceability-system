# Roadmap: AI-Native Traceability System

## MVP Status: Near Complete

### Done
- [x] Event log (JSONL append-only, .trace/events.jsonl)
- [x] NetworkX graph projection (rebuilt from events on load)
- [x] Query tools: trace, impact, orphans, decisions, proposed_links
- [x] Discovery tools: list_artifacts, search_artifacts
- [x] Write tools: add_artifact, propose_link, accept_proposal
- [x] Proposal workflow (AI proposes, human approves)
- [x] MCP server (14 tools, project-scoped config)
- [x] Methodology templates (systems-engineering, agile, lightweight)
- [x] Template tools: list_templates, get_template, apply_template, classify_artifact
- [x] Docs reorganized (SE directory structure)
- [x] Auto-reload on events.jsonl change
- [x] Dogfooding (system traces itself)

### MVP Blockers (Task 010) — ✅ COMPLETE
- [x] Bootstrap scan respects .gitignore (REQ-ALC-001)
- [x] Bootstrap scan uses git ls-files (REQ-ALC-002)
- [x] Template classification applied during registration (REQ-ALC-005)

---

## v0.2: Infrastructure & Robustness — ✅ COMPLETE

See: [v0.2 Requirements](requirements/v0.2_requirements.md)

- [x] REQ-HC-001: Health check MCP tool
- [x] REQ-ALC-003: File deletion detection
- [x] REQ-ALC-004: File rename detection
- [x] REQ-CD-001: sync_with_git MCP tool
- [x] REQ-BA-001: Batch approval tools

---

## v0.3: Adoption & AI-First Workflows

See: [v0.3 Requirements](requirements/v0.3_requirements.md)

- [x] REQ-INIT-001: One-command `trace init`
- [ ] REQ-SKILL-001: CC skill file for auto-capture
- [ ] REQ-AUTO-001: Auto-registration on file create
- [ ] REQ-IMPACT-001: Proactive impact warnings
- [ ] REQ-INFER-001: Relationship inference from imports

---

## v0.4: Anchors & Drift

- [ ] In-file anchors (section headings, functions)
- [ ] Content hash tracking
- [ ] Drift detection and alerts

---

## Future / Backlog

### GitHub Integration
- Artifact type: `issue` for GitHub Issues
- Auto-link: code referencing `#123` proposes link to issue artifact
- Bi-directional sync: trace shows implementations, GitHub shows linked artifacts
- Potential: Projects v2 custom fields for requirement status, verification state
- Prerequisite: Stable baseline, post-MVP

### Data Science / Reproducible Research Template

**Purpose:** Support researchers and scientists documenting reproducible research workflows.

**Artifact types:**
- `research_question` — Core questions being investigated
- `literature_review` — Prior work, citations, synthesis
- `methodology` — Experimental design, statistical approach
- `dataset` — Data sources, collection methods, preprocessing
- `notebook` — Jupyter notebooks, analysis code
- `analysis` — Statistical analysis, model results
- `finding` — Key findings, interpretations
- `report` — Papers, reports, presentations

**Relationship chains:**
- research_question → literature_review (informed_by)
- methodology → research_question (addresses)
- dataset → methodology (supports)
- notebook → dataset (analyzes)
- analysis → notebook (derives_from)
- finding → analysis (derives_from)
- report → finding (documents)

**Directory structure (recommended):**
```
docs/
  questions/        # Research questions, hypotheses
  literature/       # Literature review, references
  methodology/      # Study design, protocols
data/
  raw/              # Original data (may be gitignored)
  processed/        # Cleaned/transformed data
notebooks/          # Jupyter notebooks
analysis/           # Scripts, statistical code
reports/            # Papers, presentations, deliverables
```

**Use cases:**
- Academic research projects
- Data science team workflows
- Lab notebooks with traceability
- Reproducibility audits (trace from finding back to raw data)

**Prerequisite:** v0.3 complete (template infrastructure mature)

### Other Ideas
- **Data flow / architecture diagram generation** — Add runtime relationship types (`CALLS`, `SENDS_TO`, `TRANSFORMS`), finer granularity (functions not just files), optional data type annotations on edges
- CLI wrapper for MCP tools
- VS Code extension
- Web dashboard for trace visualization
- Neo4j export for complex graph queries
- Bibliography and citation tracking
- Multi-project graphs (cross-repo traceability)
- Git hook integration (auto-register on commit)
- Compliance report generation

---

## Research: Existing Context Managers

**Principle:** Adopt before create. Don't reinvent what exists.

### Investigated (2025-01-31)

| Tool | What it does | Gap for us |
|------|--------------|------------|
| `ccmem` | Project memory (settings, architecture, stories, tasks) | No relationships, no impact queries |
| `mcp-memory-keeper` | Persistent context, checkpoints | No typed relationships |
| `mcp-memory-service` | Semantic search, vector DB | Heavy, no relationship graph |
| `claude-mem` | Auto-capture, AI compression | Session-focused, not artifact-focused |
| `claude-cognitive` | Attention-based file injection | File-level only, no anchors |
| `@modelcontextprotocol/server-memory` | Official Anthropic, knowledge graph | Basic entities, no traceability semantics |

**Conclusion:** Existing tools handle *what exists*. None handle *how things relate* with typed edges, impact queries, or drift detection.

**Decision:** Build all-in-one. No dependencies on other memory systems.

---

## Out of Scope (Explicit)

- Compliance-first workflows (DOORS replacement for enterprises)
- Real-time collaboration features
- Cloud-hosted service
- GUI-first design

---

*This roadmap will evolve. Ideas welcome, scope discipline required.*
