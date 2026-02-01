# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Native Traceability System — an AI-first semantic traceability tool where relationships between project artifacts (requirements, code, tests, decisions) are captured as you work, not after. Think "modern DOORS" but graph-centric and AI-assisted.

**Current status:** Design/specification phase. Comprehensive design docs exist in `docs/` but no source code has been implemented yet. Implementation should follow the milestone plan in the detailed design spec.

## Architecture

The system is **event-sourced** and **graph-centric** with a **local-first** deployment model.

Core axiom: *Artifacts are inputs. Relationships are the system.*

**Component flow:**
```
Creator Tools → Artifact Registry → Event Log (source of truth) → Graph Projection Store → MCP Interface → Consumers
                      ↓                    ↑
               AI Assistance Service ──────┘ (proposals only)
```

Key architectural boundaries:
- **Event Log** is the immutable source of truth; the Graph Projection is rebuildable from it
- **AI never writes authoritative state** — it only creates `proposed` edges that require human acceptance
- Every relationship has a `state` (`proposed` | `authoritative`), `evidence`, and `confidence` score
- All mutations are recorded as typed events (`NODE_ADDED`, `EDGE_ADDED`, `PROPOSAL_ACCEPTED`, etc.)

**Data model:** Artifacts (requirement, decision, module, test, spec, etc.) connected by typed relationships (implements, verifies, depends_on, specifies, justifies, relates_to).

**MCP tools:** Read tools (trace, impact, orphans, history, coverage) and write tools (propose_links, accept_proposal, reject_proposal).

## Technology Stack

Planned: Python (per .gitignore patterns), with Neo4j or equivalent graph store. Jupyter notebook support for analysis.

## Design Documents

All in `docs/`:
- `ai_native_traceability_system_top_level_vision_plan.md` — vision, objectives, 5-phase roadmap
- `system_requirements_specification_*.md` — functional (FR-1–FR-17) and non-functional requirements
- `architecture_specification_*.md` — component, data, event, and deployment architecture with Mermaid diagrams
- `detailed_design_specification_*.md` — data model, services, MCP interface, implementation milestones
- `concept_of_operations_conops_*.md` — usage scenarios and operational policies
- `analysis_of_alternatives_*.md` — market analysis justifying the BUILD decision

## Implementation Milestones

1. **Minimal Core** — Event log, projection, minimal schema, manual artifact registration, MCP read tools (trace/impact/orphans)
2. **AI Proposals** — Proposal generation, accept/reject workflow, evidence + confidence
3. **Temporal Features** — Rewind, diff, history queries
4. **Packaging** — Containerized stack, local-first defaults, optional git sync
5. **Visualization** — Timeline playback, graph evolution animation
