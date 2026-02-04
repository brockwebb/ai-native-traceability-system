# Traceability MCP Server

28 tools for AI-native traceability.

## Quick Start

```bash
pip install -e ".[mcp]"
trace-mcp --project-dir /path/to/project
```

## Tool Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Query | 5 | Read graph data (trace, impact, orphans, decisions, proposed_links) |
| Discovery | 2 | Find artifacts (list_artifacts, search_artifacts) |
| Write | 2 | Create artifacts/links (add_artifact, propose_link) |
| Approval | 4 | Promote to authoritative (accept_proposal, accept_all_proposed, accept_by_type, accept_by_source) |
| Template | 4 | Methodology support (list_templates, get_template, apply_template, classify_artifact) |
| Maintenance | 2 | Data integrity (health_check, sync_with_git) |
| Automation | 3 | AI-first capture - v0.3 (register_file, check_impact, infer_dependencies) |
| Reports | 6 | Human-facing outputs - v0.4 (export_mermaid, export_dependency_map, export_coverage_report, export_rtm, export_impact_report, export_decision_log) |

**Total: 28 tools**

## Documentation

- [User Guide](../docs/user-guide/) - Quick start, concepts, workflows
- [MCP Tools Reference](../docs/reference/mcp-tools.md) - Complete API documentation
- [Automatic Capture](../docs/user-guide/automatic-capture.md) - What happens invisibly
- [Reports & Queries](../docs/user-guide/reports-and-queries.md) - Human-facing outputs

## Configuration

Add to Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

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

## Architecture

- **Event log**: Append-only `.trace/events.jsonl`
- **Graph**: NetworkX projection rebuilt from events
- **Authority model**: AI writes "proposed", human approves to "authoritative"
- **State**: Reloads automatically when events file changes

## Version History

- **v0.1.0** - MVP: Core graph operations, MCP server
- **v0.2.0** - Infrastructure: Health checks, git sync, batch approvals
- **v0.3.0** - Automation: Auto-capture, impact warnings, dependency inference
- **v0.4.0** - Reports: RTM, coverage, dependency maps, impact analysis
