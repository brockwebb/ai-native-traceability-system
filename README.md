# AI-Native Traceability System

Project memory that survives context windows, thread death, and human absence.

## What It Does

**Automatic (invisible):**
- Registers files as you create them
- Tracks dependencies from imports
- Links tests to code, code to requirements
- Warns before high-impact changes

**Human-facing (on request):**
- Dependency visualizations (Mermaid, Graphviz)
- Requirements Traceability Matrix
- Coverage gap analysis
- Impact reports for change management

## Quick Start

```bash
pip install -e ".[mcp]"
cd your-project
trace init
```

Then work with Claude Code—everything captures automatically.

## How It Works

```
your-project/
├── .trace/
│   └── events.jsonl    # Append-only event log (git-tracked)
├── .mcp.json           # MCP server config (project-scoped)
└── .claude/
    └── skills/
        └── traceability.md  # Claude Code instructions
```

- **Event log**: Human-readable, git-diffable, no database
- **Graph**: Rebuilt in-memory (NetworkX) from events on load
- **Authority model**: AI writes "proposed", human approves in batches

## MCP Tools (28 total)

### Core Operations (6)
- `add_artifact`, `propose_link` - Write operations
- `accept_proposal`, `accept_all_proposed`, `accept_by_type`, `accept_by_source` - Approval

### Discovery & Queries (7)
- `list_artifacts`, `search_artifacts` - Find things
- `trace`, `impact`, `orphans` - Relationship queries
- `decisions`, `proposed_links` - Status queries

### Automation (3) - v0.3
- `register_file` - Auto-classify and register files
- `check_impact` - Pre-modification warnings
- `infer_dependencies` - Parse imports, propose links

### Reports (6) - v0.4
- `export_mermaid`, `export_dependency_map` - Visualizations
- `export_rtm` - Requirements Traceability Matrix
- `export_coverage_report` - Gap analysis
- `export_impact_report` - Change impact with risk assessment
- `export_decision_log` - Decision history

### Methodology & Maintenance (6)
- `list_templates`, `get_template`, `apply_template`, `classify_artifact` - Template support
- `health_check`, `sync_with_git` - Data integrity

## Documentation

- [Quick Start](docs/user-guide/quick-start.md) - Get running in 5 minutes
- [Automatic Capture](docs/user-guide/automatic-capture.md) - What happens invisibly
- [Reports & Queries](docs/user-guide/reports-and-queries.md) - Human-facing outputs
- [Concepts](docs/user-guide/concepts.md) - Artifacts, links, authority model
- [Workflows](docs/user-guide/workflows.md) - Common usage patterns
- [MCP Tools Reference](docs/reference/mcp-tools.md) - All 28 tools

## Version History

- **v0.1.0** - MVP: Core graph, MCP server
- **v0.2.0** - Infrastructure: Health checks, git sync
- **v0.3.0** - Automation: Auto-capture, impact warnings
- **v0.4.0** - Reports: RTM, coverage, dependency maps

## Status

**Alpha (v0.4.0).** Core functionality complete. This repo traces itself.

## License

MIT
