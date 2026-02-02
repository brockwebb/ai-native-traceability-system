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

### MVP Blockers (Task 010)
- [ ] Bootstrap scan respects .gitignore (REQ-ALC-001)
- [ ] Bootstrap scan uses git ls-files (REQ-ALC-002)
- [ ] Template classification applied during registration (REQ-ALC-005)

---

## v0.2: Change Detection

- [ ] File deletion detection (REQ-ALC-003)
- [ ] File rename/move detection via git (REQ-ALC-004)
- [ ] sync_with_git MCP tool
- [ ] Batch approval MCP tool

---

## v0.3: Anchors & Drift

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
