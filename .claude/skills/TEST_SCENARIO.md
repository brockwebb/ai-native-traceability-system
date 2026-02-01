# Traceability Skill - Test Scenarios

This document demonstrates how Claude Code should behave with the traceability skill active.

## Scenario 1: User Requests New Feature

**User:** "Add a new utility module for string formatting in src/utils/formatters.py"

**Claude's Response (with skill):**

```
I'll create a string formatting utility module.

[Creates src/utils/formatters.py with formatting functions]

[Skill activates: New file created → Register artifact]
[Calls MCP: add_artifact("src/utils/formatters.py", "module", "src/utils/formatters.py")]

✓ Created src/utils/formatters.py with formatting utilities.
✓ Registered as artifact in trace system.

1 artifact added. Use proposed_links() to review when ready.
```

## Scenario 2: User Requests Test Creation

**User:** "Write tests for the formatters module"

**Claude's Response (with skill):**

```
I'll create comprehensive tests for the formatters module.

[Creates tests/test_formatters.py]

[Skill activates: New test file → Register + Link to code]
[Calls MCP: add_artifact("tests/test_formatters.py", "test", "tests/test_formatters.py")]
[Calls MCP: propose_link("tests/test_formatters.py", "src/utils/formatters.py", "verifies", "Tests string formatting utilities")]

✓ Created tests/test_formatters.py
✓ Registered test artifact
✓ Linked test to src/utils/formatters.py

All tests passing!

1 artifact, 1 link proposed. Use proposed_links() to review.
```

## Scenario 3: User Requests Refactoring

**User:** "Refactor the TraceGraph class to improve performance"

**Claude's Response (with skill):**

```
Let me check what depends on TraceGraph first.

[Skill activates: Before refactoring → Check impact]
[Calls MCP: impact("src/trace_core/graph.py")]

Impact analysis shows:
- queries.py depends on this
- server.py depends on this
- test_graph.py tests this

I'll refactor while maintaining the public API.

[Makes changes to src/trace_core/graph.py]
[Runs test_graph.py to verify]

✓ Refactored TraceGraph
✓ All tests passing
✓ Dependencies still satisfied

No new artifacts or links needed (existing links remain valid).
```

## Scenario 4: User Documents Design Decision

**User:** "Document why we chose to use file paths as artifact IDs"

**Claude's Response (with skill):**

```
I'll add this to the design decisions document.

[Updates docs/design_decisions_2025-02-01.md with new section]

[Skill activates: Decision doc updated → May need to link to code]
[Checks: Does design_decisions artifact exist?]
[Calls MCP: trace("docs/design_decisions_2025-02-01.md")]
[Result: Already exists, already linked to models.py]

✓ Documented ID convention decision
✓ Artifact already tracked, no new links needed

Design decision recorded. Existing link to models.py covers this.
```

## Scenario 5: User Implements Requirement

**User:** "Implement the orphan detection feature from FR-7"

**Claude's Response (with skill):**

```
[Checks for requirement doc first]
[Calls MCP: trace("docs/requirements.md#FR-7")]
[Result: Not found - requirement not registered yet]

I'll implement the orphan detection feature.

[Adds orphans() method to queries.py]

[Skill activates: Implementation of feature → Link to requirement]
[But requirement doc doesn't exist in trace yet, so just document the intent]

✓ Implemented orphans() method in queries.py
✓ Added comprehensive tests in test_queries.py

Note: If you have a requirements document for FR-7, I can link this implementation to it.
For now, the implementation is ready and tested.

Modified existing artifacts, no new links proposed.
```

## Scenario 6: User Adds Dependency

**User:** "Update server.py to use a new validation helper from utils/validators.py"

**Claude's Response (with skill):**

```
I'll create the validation helper and update the server.

[Creates src/utils/validators.py]
[Calls MCP: add_artifact("src/utils/validators.py", "module", ...)]

[Updates mcp_server/server.py to import from validators]

[Skill activates: New dependency → Create depends_on link]
[Calls MCP: propose_link("mcp_server/server.py", "src/utils/validators.py", "depends_on", "Uses validators for input validation")]

✓ Created src/utils/validators.py
✓ Updated server.py to use validation helpers
✓ Linked dependency: server.py → validators.py

1 artifact, 1 link proposed. Use proposed_links() to review.
```

## Scenario 7: End of Session Summary

**User:** "Thanks, I'm done for now"

**Claude's Response (with skill):**

```
You're welcome! Here's what we worked on:

Created:
- src/utils/formatters.py
- tests/test_formatters.py
- src/utils/validators.py

Modified:
- mcp_server/server.py (added validation)

Traceability:
✓ 3 artifacts registered
✓ 2 links proposed (test→code, code→dependency)

Proposed links await approval:
1. tests/test_formatters.py → src/utils/formatters.py (verifies)
2. mcp_server/server.py → src/utils/validators.py (depends_on)

To review and approve:
- Run: proposed_links() to see all pending
- Accept: accept_proposal(source_id, target_id)

All changes committed to git.
```

## Anti-Example: Over-Capture

**User:** "Fix typo in README.md"

**Claude's Response (with skill):**

```
[Fixes typo in README.md]

✓ Fixed typo in README.md

[Skill does NOT activate - this is a minor edit, not structural]
[No artifact registration, no links - just a simple fix]
```

## Anti-Example: Don't Link External Dependencies

**User:** "Add networkx import to graph.py"

**Claude's Response (with skill):**

```
[Adds import networkx as nx to graph.py]

✓ Added networkx import

[Skill does NOT activate - external library, not repo artifact]
[No link to networkx - only trace relationships within the repo]
```

## Verification Commands

After any of these scenarios, verify the skill worked:

```bash
# See all artifacts
python scripts/query_trace.py

# Check specific artifact
python -c "
from mcp_server.server import TraceabilityServer
s = TraceabilityServer('.trace')
print(s._handle_trace('src/utils/formatters.py'))
"

# Review proposed links
python -c "
from mcp_server.server import TraceabilityServer
s = TraceabilityServer('.trace')
print(s._handle_proposed_links())
"
```

## Success Indicators

The skill is working correctly if Claude:
1. ✅ Registers new files automatically
2. ✅ Links tests to code without being asked
3. ✅ Checks impact before refactoring
4. ✅ Doesn't over-capture trivial changes
5. ✅ Reminds about pending approvals at end
6. ✅ Uses file paths as IDs (not absolute paths)
7. ✅ Provides specific rationales for links

## Failure Indicators

The skill needs adjustment if Claude:
1. ❌ Forgets to register new files
2. ❌ Creates tests but doesn't link them
3. ❌ Refactors without checking impact
4. ❌ Captures every tiny edit
5. ❌ Uses absolute paths as IDs
6. ❌ Creates vague rationales ("links to code")
7. ❌ Doesn't mention pending approvals

---

**Next:** Test these scenarios in a real Claude Code session to verify behavior.
