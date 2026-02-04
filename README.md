# AI-Native Traceability System

Project memory infrastructure for AI-assisted development. Captures relationships between artifacts (requirements, code, tests, decisions) as you work — survives context windows, thread death, and human absence.

## The Problem

LLM context limits create constant overhead. Every new thread starts near-zero. Every long thread drifts. You become RAM, reloading Claude with "remember, the architecture is HERE, the decision about X was THIS."

Same problem after time gaps — returning to a project after weeks means archaeology to recover what exists and why.

## The Solution

A lightweight traceability graph that lives in your repo:
- **Decisions captured as they happen**, not in a separate documentation phase
- **Impact queries**: "what depends on this requirement?"
- **Artifact registry**: "where is the auth module?"
- **AI-first capture**: Auto-registers files, infers dependencies, warns about impact
- **Break-fix history**: "we tried X, it broke Y, we reverted"

Claude queries the graph via MCP tools. Context survives thread death.

## Quick Start

### 1. Install

```bash
# Clone and install in editable mode (PyPI coming soon)
git clone https://github.com/brockwebb/ai-native-traceability-system.git
cd ai-native-traceability-system
pip install -e ".[mcp]"
```

### 2. Initialize a Project

```bash
cd /path/to/your/project
trace init
```

This creates:
- `.trace/` directory with event log
- `.mcp.json` for MCP server configuration
- `.claude/skills/traceability.md` skill file for Claude Code

### 3. Configure Claude Desktop (if using)

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trace": {
      "command": "trace-mcp",
      "args": ["--project-dir", "/path/to/your/project"]
    }
  }
}
```

### 4. Start Working

Claude Code automatically captures traceability data as you work.
The skill file instructs CC to:
- Register new files as artifacts
- Check impact before modifications
- Link tests to code
- Link implementations to requirements

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

## MCP Tools (22 total)

### Core Operations
- `add_artifact` - Register artifacts with type, tags, file location
- `propose_link` - Create relationships between artifacts
- `accept_proposal` / `accept_all_proposed` / `accept_by_type` / `accept_by_source` - Approve links

### Discovery & Queries
- `list_artifacts` - List all artifacts (optional type filter)
- `search_artifacts` - Search by name, path, type, or tags
- `trace` - Get upstream/downstream neighbors
- `impact` - Transitive downstream (what breaks if this changes?)
- `orphans` - Find unconnected artifacts

### Automation
- `register_file` - Auto-classify and register a file
- `check_impact` - Warn if downstream dependencies exceed threshold
- `infer_dependencies` - Parse imports and propose depends_on links

### Methodology
- `list_templates` / `get_template` / `apply_template` - Methodology scaffolding
- `classify_artifact` - Suggest artifact type based on file path

### Maintenance
- `health_check` - Validate trace data integrity
- `sync_with_git` - Synchronize with git repository state
- `decisions` - List all decision records
- `proposed_links` - List links awaiting approval

## Version History

- **v0.1.0** - MVP: Core graph operations, MCP server, self-dogfooding
- **v0.2.0** - Infrastructure: Health checks, git sync, batch approvals
- **v0.3.0** - Adoption: Global install, `trace init`, auto-capture, impact warnings
- **v0.4.0** - Reports & Visualization (planned)
- **v0.5.0** - Analysis Integration & Enrichment (planned)

## Documentation

- **[Quick Start](docs/user-guide/quick-start.md)** - Get running in 5 minutes
- **[Concepts](docs/user-guide/concepts.md)** - Understand artifacts, links, authority model
- **[Workflows](docs/user-guide/workflows.md)** - Common usage patterns
- **[CLI Reference](docs/reference/cli.md)** - All CLI commands
- **[MCP Tools Reference](docs/reference/mcp-tools.md)** - All 22 MCP tools

## Status

**Alpha (v0.3.0).** Core functionality complete. This repo traces itself.

## License

MIT
