# Traceability MCP Server

MCP server that exposes traceability tools to Claude.

## Installation

```bash
pip install -e .
```

## Running the Server

The server can be started using the `trace-mcp` command:

```bash
trace-mcp
```

By default, the server uses `.trace` in the current directory for storage. You can customize this with the `TRACE_DIR` environment variable:

```bash
TRACE_DIR=/path/to/trace trace-mcp
```

## Configuring Claude Desktop

Add this to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "trace": {
      "command": "trace-mcp",
      "env": {
        "TRACE_DIR": ".trace"
      }
    }
  }
}
```

## Available Tools

### Read-Only Queries

1. **trace** - Get upstream and downstream neighbors of an artifact
   - Input: `artifact_id` (string)
   - Returns: `{artifact_id, upstream[], downstream[]}`

2. **impact** - Get all artifacts affected if this artifact changes (transitive downstream)
   - Input: `artifact_id` (string)
   - Returns: `{artifact_id, affected_artifacts[], count}`

3. **orphans** - Find artifacts with no incoming or outgoing relationships
   - Input: none
   - Returns: `{orphan_artifacts[], count}`

4. **decisions** - Get all decision records
   - Input: none
   - Returns: `{decisions[], count}`

5. **proposed_links** - Get all links awaiting approval (proposed state)
   - Input: none
   - Returns: `{proposed_links[], count}`

### Write Operations

6. **add_artifact** - Register a new artifact in the trace system
   - Input: `artifact_id`, `artifact_type`, optional: `file_path`, `line_start`, `content_hash`
   - Returns: `{success, artifact_id, state}`

7. **propose_link** - Create a proposed link between two artifacts
   - Input: `source_id`, `target_id`, `relationship_type`, `rationale`
   - Returns: `{success, source, target, relationship_type, state}`

8. **accept_proposal** - Promote a proposed link to authoritative state
   - Input: `source_id`, `target_id`
   - Returns: `{success, source, target, state}`

## Artifact Types

- `requirement` - Requirements/specifications
- `decision` - Design decisions
- `module` - Code modules/packages
- `function` - Functions/methods
- `test` - Test cases
- `document` - Documentation
- `issue` - Issues/bugs

## Relationship Types

- `implements` - Code implements requirement
- `depends_on` - A depends on B
- `verifies` - Test verifies requirement/code
- `supersedes` - New decision supersedes old
- `contains` - Parent contains child
- `references` - Generic reference

## Authority Model

- **Proposed** - AI-generated links/artifacts, awaiting approval
- **Authoritative** - Human-approved, committed to memory

All write operations by AI create proposed items. Use `accept_proposal` to promote links to authoritative state.

## Example Usage

```python
# In Claude Desktop, these tools become available:

# Add artifacts
add_artifact(artifact_id="FR-1", artifact_type="requirement")
add_artifact(artifact_id="auth_module", artifact_type="module")

# Create link
propose_link(
    source_id="FR-1",
    target_id="auth_module",
    relationship_type="implements",
    rationale="auth_module implements authentication requirement FR-1"
)

# Query
trace(artifact_id="auth_module")  # See what connects to it
impact(artifact_id="FR-1")        # See what breaks if FR-1 changes

# Approve
accept_proposal(source_id="FR-1", target_id="auth_module")
```

## Storage

All data is stored in `.trace/events.jsonl` as append-only JSON lines. The file is:
- Human-readable
- Git-diffable
- No binary formats
- Survives process restarts

The graph is rebuilt from events on server start.
