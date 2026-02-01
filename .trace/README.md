# Traceability Graph - Repository Self-Trace

This directory contains the traceability graph for this repository itself (dogfooding).

## Contents

- **events.jsonl** - Append-only event log (32 events)
  - 12 artifacts registered
  - 10 links created and approved
  - All links promoted to authoritative state

## Artifacts Registered

### Documentation
- `design_decisions` - docs/design_decisions_2025-01-31.md (decision)
- `vision_plan` - docs/ai_native_traceability_system_top_level_vision_plan.md (requirement)
- `claude_md` - CLAUDE.md (document)

### Core Library
- `models.py` - src/trace_core/models.py (module)
- `events.py` - src/trace_core/events.py (module)
- `graph.py` - src/trace_core/graph.py (module)
- `queries.py` - src/trace_core/queries.py (module)

### MCP Server
- `server.py` - mcp_server/server.py (module)

### Tests
- `test_events.py` - tests/test_events.py (test)
- `test_graph.py` - tests/test_graph.py (test)
- `test_queries.py` - tests/test_queries.py (test)
- `test_mcp_server.py` - tests/test_mcp_server.py (test)

## Dependency Chain

```
vision_plan → design_decisions → models.py → events.py → graph.py → queries.py → server.py
```

## Test Coverage

```
test_events.py     → events.py    (verifies)
test_graph.py      → graph.py     (verifies)
test_queries.py    → queries.py   (verifies)
test_mcp_server.py → server.py    (verifies)
```

## Impact Analysis

Changing `models.py` affects:
- events.py
- graph.py
- queries.py
- server.py

## Orphans

- `claude_md` - Documentation file with no traced dependencies (expected)

## Querying This Data

```bash
# Start MCP server
trace-mcp

# Or use programmatically
python -c "
from mcp_server.server import TraceabilityServer
server = TraceabilityServer('.trace')
print(server._handle_trace('models.py'))
"
```

## Generated

- Date: 2026-02-01
- By: scripts/dogfood_trace.py
- Total events: 32
- All links: authoritative (human-approved)
