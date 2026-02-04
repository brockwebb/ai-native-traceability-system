# Quick Start

Get traceability running in 5 minutes.

## Prerequisites

- Python 3.11+
- Git (for sync features)
- Claude Code or Claude Desktop (for MCP integration)

## Install

```bash
# Clone and install (PyPI coming soon)
git clone https://github.com/brockwebb/ai-native-traceability-system.git
cd ai-native-traceability-system
pip install -e ".[mcp]"
```

## Initialize Your Project

```bash
cd /path/to/your/project
trace init
```

This creates:
- `.trace/events.jsonl` - Append-only event log
- `.mcp.json` - MCP server configuration
- `.claude/skills/traceability.md` - Claude Code automation rules

## Verify It Works

```bash
# Check status
trace status

# Start MCP server (for testing)
trace-mcp --project-dir .
```

## Use With Claude Code

Just start working. The skill file instructs Claude Code to:
1. Register new files automatically
2. Check impact before modifications
3. Link tests to code
4. Link implementations to requirements

## Use With Claude Desktop

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

Then ask Claude:
- "What depends on the auth module?"
- "Show me orphan requirements"
- "Log decision: we chose X because Y"

## Next Steps

- [Concepts](concepts.md) - Understand artifacts, links, authority model
- [CLI Reference](../reference/cli.md) - All CLI commands
- [MCP Tools Reference](../reference/mcp-tools.md) - All 22 MCP tools
