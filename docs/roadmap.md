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

## v0.2: Infrastructure & Robustness

See: [v0.2 Requirements](requirements/v0.2_requirements.md)

- [ ] REQ-HC-001: Health check MCP tool
- [ ] REQ-ALC-003: File deletion detection
- [ ] REQ-ALC-004: File rename detection
- [ ] REQ-CD-001: sync_with_git MCP tool
- [ ] REQ-BA-001: Batch approval tools

---

## v0.3: Adoption & AI-First Workflows

See: [v0.3 Requirements](requirements/v0.3_requirements.md)

- [ ] REQ-INIT-001: One-command `trace init`
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
