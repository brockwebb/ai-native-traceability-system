# Traceability MCP Server

MCP server that exposes 10 traceability tools to Claude.

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

### Discovery Tools

6. **list_artifacts** - List all registered artifacts
   - Input: optional `artifact_type` filter
   - Returns: `{artifacts: [{id, type, file_path, tags}, ...], count}`

7. **search_artifacts** - Search artifacts by name, path, type, or tags
   - Input: `query` (substring), `artifact_type`, `tags` (any match)
   - Returns: `{matches: [{id, type, file_path, tags}, ...], count}`

### Write Operations

8. **add_artifact** - Register a new artifact in the trace system
   - Input: `artifact_id`, `artifact_type`, optional: `file_path`, `line_start`, `content_hash`, `tags`
   - Returns: `{success, artifact_id, state}`

9. **propose_link** - Create a proposed link between two artifacts
   - Input: `source_id`, `target_id`, `relationship_type`, `rationale`
   - Returns: `{success, source, target, relationship_type, state}`

10. **accept_proposal** - Promote a proposed link to authoritative state
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

## Discovery & Search

Find artifacts without knowing their exact IDs:

```python
# Add artifacts with tags for easier discovery
add_artifact(
    artifact_id="roadmap-2026",
    artifact_type="document",
    file_path="docs/roadmap.md",
    tags=["planning", "future", "vision"]
)

# List all artifacts
list_artifacts()

# List artifacts by type
list_artifacts(artifact_type="requirement")

# Search by substring (case-insensitive)
search_artifacts(query="auth")  # Finds "auth_module", "user-authentication", etc.

# Search by tags
search_artifacts(tags=["planning", "future"])  # Finds artifacts with ANY of these tags

# Combined search
search_artifacts(
    query="user",
    artifact_type="requirement",
    tags=["security"]
)
```

### Tags

Tags make artifacts discoverable:
- Add multiple tags when creating artifacts
- Search finds artifacts with ANY matching tag (OR logic)
- Tags persist through event log reload
- Optional - existing code works without tags

## Storage

All data is stored in `.trace/events.jsonl` as append-only JSON lines. The file is:
- Human-readable
- Git-diffable
- No binary formats
- Survives process restarts

The graph is rebuilt from events on server start.
