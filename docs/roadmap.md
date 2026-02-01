# Product Roadmap — AI-Native Traceability System

## Paradigm

**Working baseline > new features**

In AI-assisted development, code generates faster than humans comprehend. Structure prevents the spaghetti mess that "working code" becomes without traceability.

---

## MVP (v0.1) — Core Memory System

The minimum to be useful on a real project (this one).

- [ ] Event log (`events.jsonl`) — append-only, JSONL format
- [ ] NetworkX projection — rebuild graph from events on load
- [ ] Core queries: `trace`, `impact`, `orphans`, `decisions`, `stale`
- [ ] Anchor system with hash-based drift detection
- [ ] Parsers: Markdown headings, Python AST (functions/classes)
- [ ] MCP server exposing query tools
- [ ] Claude Code skill for capture workflow
- [ ] Dogfood: trace this repo's own development

**Exit criteria:** Can answer "what depends on X" and "what did we decide about Y" across thread boundaries.

---

## v0.2 — Methodology Templates

For people who want guidance on what artifacts to produce.

- [ ] Template library concept (systems engineering, agile, lightweight)
- [ ] Artifact checklists per methodology
- [ ] Document skeletons (SRS, architecture, decision log, etc.)
- [ ] "Start project" flow suggests artifacts based on chosen methodology
- [ ] Non-enforcing — suggestions, not gates

---

## Future — Ideas Parking Lot

Captured to prevent scope creep. Evaluate after MVP works.

- Bibliography and citation tracking
- Multi-project graphs (cross-repo traceability)
- Visualization (timeline replay, graph explorer)
- Neo4j projection option for complex queries
- Git hook integration (auto-register on commit)
- VS Code extension
- Compliance report generation (for those who need it)

---

## Research: Existing Context Managers

**Principle:** Adopt before create. Don't reinvent what exists.

This system is a *specific* context manager — traceability-focused, relationship-centric. But the broader ecosystem of AI memory/context tools may have reusable patterns or integrations.

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

### Rationale for All-In-One

- **Installation friction kills adoption** — one install, everything works
- **Existing tools are passive** — require explicit calls, no auto-capture
- **Generic memory ≠ traceability** — we need typed relationships, impact queries, anchors
- **Modular internals** — others can borrow our patterns if useful

### Patterns to Adopt (with credit)

- Hook-based auto-capture (from ccmem)
- CLI UX: `setup`, `status`, `search` (from ccmem)
- MCP tool structure (from official server-memory)
- All source projects are MIT licensed — credit in README

### Integration Considerations

- Could this plug into a broader context manager as a "traceability module"?
- Should the event log format be compatible with other memory systems?
- MCP is the interface layer — does that provide natural integration?

---

## Out of Scope (Explicit)

- Compliance-first workflows (DOORS replacement for enterprises)
- Real-time collaboration features
- Cloud-hosted service
- GUI-first design

---

*This roadmap will evolve. Ideas welcome, scope discipline required.*
