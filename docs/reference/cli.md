# CLI Reference

## trace init

Initialize traceability in a project.

```bash
trace init [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--template NAME` | Force specific template (systems-engineering, agile, lightweight) |
| `--skip-bootstrap` | Don't scan existing files |
| `--skip-mcp` | Don't create .mcp.json |
| `--skip-skill` | Don't create skill file |
| `--dry-run` | Show what would be created |
| `--force` | Overwrite existing files |

**Creates:**
- `.trace/events.jsonl` - Event log
- `.trace/templates/` - Methodology templates
- `.mcp.json` - MCP configuration
- `.claude/skills/traceability.md` - CC automation rules

**Auto-detection:**
- `docs/requirements/` → systems-engineering
- `stories/` or `sprints/` → agile
- Otherwise → lightweight

## trace status

Show current trace state.

```bash
trace status
```

**Output:**
- Artifact count by type
- Link count by relationship type
- Pending approvals
- Last event timestamp

## trace-mcp

Start the MCP server.

```bash
trace-mcp [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--project-dir PATH` | Project root (default: current directory) |

**Environment:**
| Variable | Description |
|----------|-------------|
| `TRACE_DIR` | Override .trace location |
