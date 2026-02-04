# Traceability MCP Server

MCP server exposing 22 traceability tools to Claude.

## Quick Start

```bash
# Install
pip install -e ".[mcp]"

# Run server
trace-mcp --project-dir /path/to/project
```

## Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

## Tools Overview

| Category | Tools | Purpose |
|----------|-------|---------|
| Query | trace, impact, orphans, decisions, proposed_links | Read graph data |
| Discovery | list_artifacts, search_artifacts | Find artifacts |
| Write | add_artifact, propose_link | Create artifacts/links |
| Approval | accept_proposal, accept_all_proposed, accept_by_type, accept_by_source | Promote to authoritative |
| Template | list_templates, get_template, apply_template, classify_artifact | Methodology support |
| Maintenance | health_check, sync_with_git | Data integrity |
| Automation | register_file, check_impact, infer_dependencies | AI-first capture |

See [MCP Tools Reference](../docs/reference/mcp-tools.md) for complete documentation.

## Storage

All data in `.trace/events.jsonl`:
- Append-only JSON lines
- Human-readable, git-diffable
- Graph rebuilt from events on load
