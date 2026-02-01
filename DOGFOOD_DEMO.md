# Dogfooding Demo - Repository Self-Trace

This repository now traces its own artifacts and dependencies using the traceability system!

## Quick Start

### View the trace data
```bash
# Human-readable event log
cat .trace/events.jsonl | python -m json.tool | less

# Summary
cat .trace/README.md
```

### Query the trace

**Option 1: Use the query script**
```bash
python scripts/query_trace.py
```

**Option 2: Use Python directly**
```python
from mcp_server.server import TraceabilityServer

server = TraceabilityServer(".trace")

# What depends on models.py?
print(server._handle_trace("models.py"))

# What breaks if design_decisions change?
print(server._handle_impact("design_decisions"))

# Find orphaned artifacts
print(server._handle_orphans())
```

**Option 3: Use MCP server (with Claude Desktop)**
```bash
# Start server
trace-mcp

# Then in Claude Desktop:
# "What artifacts are traced in this repository?"
# "What would break if I change models.py?"
# "Show me the dependency chain"
```

## What's Traced

### 12 Artifacts
- 3 documentation files (vision, design, CLAUDE.md)
- 4 core library modules (models, events, graph, queries)
- 1 MCP server module
- 4 test files

### 10 Relationships (all authoritative ✅)
```
vision_plan ──references──> design_decisions
design_decisions ──implements──> models.py
models.py ──depends_on──> events.py
events.py ──depends_on──> graph.py
graph.py ──depends_on──> queries.py
queries.py ──depends_on──> server.py

test_events.py ──verifies──> events.py
test_graph.py ──verifies──> graph.py
test_queries.py ──verifies──> queries.py
test_mcp_server.py ──verifies──> server.py
```

## Example Queries

### "What implements the design decisions?"
```bash
$ python -c "
from mcp_server.server import TraceabilityServer
s = TraceabilityServer('.trace')
print(s._handle_trace('design_decisions'))
"
```
**Output:**
```json
{
  "artifact_id": "design_decisions",
  "upstream": ["vision_plan"],
  "downstream": ["models.py"]
}
```

### "If I change models.py, what breaks?"
```bash
$ python -c "
from mcp_server.server import TraceabilityServer
s = TraceabilityServer('.trace')
print(s._handle_impact('models.py'))
"
```
**Output:**
```json
{
  "artifact_id": "models.py",
  "affected_artifacts": ["events.py", "graph.py", "queries.py", "server.py"],
  "count": 4
}
```
**Insight:** Changing `models.py` affects the entire dependency chain!

### "Which tests cover the core library?"
All core modules have test coverage:
- ✓ test_events.py → events.py
- ✓ test_graph.py → graph.py
- ✓ test_queries.py → queries.py
- ✓ test_mcp_server.py → server.py

### "Any orphaned artifacts?"
```bash
$ python scripts/query_trace.py
```
**Result:** Only `claude_md` is orphaned (expected - it's standalone documentation)

## Regenerate the Trace

If you modify the repository structure:
```bash
rm -rf .trace
python scripts/dogfood_trace.py
git add .trace/events.jsonl
git commit -m "Update self-trace"
```

## What This Demonstrates

✅ **Project Memory** - Relationships persist across sessions
✅ **Impact Analysis** - See downstream effects before making changes
✅ **Bi-directional Tracing** - Navigate upstream (requirements) or downstream (implementations)
✅ **Git Integration** - Events are version-controlled, human-readable JSONL
✅ **Authority Model** - AI proposes, human approves (all links are authoritative)
✅ **Zero Infrastructure** - Just files + NetworkX, no database required

## Storage Format

The entire trace is in `.trace/events.jsonl` (9.7 KB, 32 events):

```bash
$ wc -l .trace/events.jsonl
32 .trace/events.jsonl

$ head -1 .trace/events.jsonl | python -m json.tool
{
  "event_id": "7701db04-aab8-422f-b871-c5b191e0cefc",
  "timestamp": "2026-02-01T14:57:09.724893+00:00",
  "event_type": "artifact_added",
  "actor": "ai:claude-code",
  "state": "proposed",
  "payload": {
    "artifact_id": "design_decisions",
    "artifact_type": "decision",
    "file_path": "docs/design_decisions_2025-01-31.md"
  }
}
```

## Next Steps

Try these queries:
```bash
# Full interactive query
python scripts/query_trace.py

# Check specific module
python -c "from mcp_server.server import TraceabilityServer; s = TraceabilityServer('.trace'); print(s._handle_trace('server.py'))"

# Verify all tests
python -c "from mcp_server.server import TraceabilityServer; s = TraceabilityServer('.trace'); print([n for n in s.graph.graph.nodes() if n.startswith('test_')])"
```

## Learn More

- **How it works:** `docs/design_decisions_2025-01-31.md`
- **MCP server:** `mcp_server/README.md`
- **Vision:** `docs/ai_native_traceability_system_top_level_vision_plan.md`
- **Implementation:** Explore `src/trace_core/`

---

**The system eats its own dog food!** 🐕🍖
