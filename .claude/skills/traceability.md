# Traceability Skill

Automatically capture artifacts and relationships during development work.

## Overview

This repository uses AI-native traceability to maintain a living graph of relationships between requirements, code, tests, and decisions. As you work, capture artifacts and links so the system builds institutional memory that survives context windows and thread death.

## When to Capture

### Auto-Capture Triggers

**Creating a new file:**
- Register with `add_artifact` using the file path as ID
- Determine artifact type from location/extension
- Include file path in metadata

**Creating a test file:**
- Register test artifact
- Propose link to the code under test (VERIFIES relationship)
- Rationale: "Tests [functionality]"

**Implementing a requirement:**
- After creating/modifying implementation
- Propose link from requirement to code (IMPLEMENTS relationship)
- Rationale: "Implements [requirement description]"

**Making a design decision:**
- Create/update decision document
- Register as artifact type "decision"
- Link to affected code (IMPLEMENTS relationship)

**Adding a dependency:**
- When a file imports/uses another
- Propose link (DEPENDS_ON relationship)
- Rationale: "[File A] depends on [File B] for [reason]"

**Refactoring/Major changes:**
- BEFORE: Check `impact(artifact_id)` to see downstream effects
- AFTER: Verify links are still valid, update if files renamed

## Artifact Type Mapping

Use these rules to determine artifact type:

```
src/**/*.py           → module
tests/**/*.py         → test
docs/**/*.md          → decision (if "decision" in title) OR requirement
handoffs/**/*.md      → document
CLAUDE.md             → document
README.md             → document
*.md (root)           → document
pyproject.toml        → document
```

## ID Conventions

**Use relative file paths as artifact IDs:**

```python
# Good IDs
"src/trace_core/models.py"
"tests/test_events.py"
"docs/design_decisions_2025-01-31.md"
"CLAUDE.md"

# For anchors within files (future enhancement)
"src/trace_core/models.py#Event"
"src/trace_core/models.py#EventType"
"docs/spec.md#FR-1"
```

**Do NOT use:**
- Absolute paths
- Generic names like "module" or "test"
- UUIDs or generated IDs

## Workflow Patterns

### Pattern A: New Implementation

When implementing a new feature or requirement:

```
1. BEFORE coding: trace(requirement_id) to understand context
   - See what else implements this requirement
   - Identify dependencies

2. CREATE file: add_artifact(file_path, "module", file_path)

3. AFTER coding: propose_link(requirement_doc, file_path, "implements", "rationale")
   - Rationale format: "Implements [specific capability] from [requirement ID]"
```

Example:
```python
# Claude is asked to implement authentication based on FR-1

# Step 1: Check context
trace("docs/requirements.md#FR-1")

# Step 2: Create implementation
# ... write src/auth/login.py ...

# Step 3: Register artifact
add_artifact(
    artifact_id="src/auth/login.py",
    artifact_type="module",
    file_path="src/auth/login.py"
)

# Step 4: Link to requirement
propose_link(
    source_id="docs/requirements.md#FR-1",
    target_id="src/auth/login.py",
    relationship_type="implements",
    rationale="Implements user authentication requirement FR-1"
)
```

### Pattern B: New Test

When creating a test file:

```
1. CREATE test: add_artifact(test_path, "test", test_path)

2. LINK to code: propose_link(test_path, code_path, "verifies", "rationale")
   - Rationale format: "Tests [specific functionality] in [module]"
```

Example:
```python
# Creating test_auth.py to test auth/login.py

add_artifact(
    artifact_id="tests/test_auth.py",
    artifact_type="test",
    file_path="tests/test_auth.py"
)

propose_link(
    source_id="tests/test_auth.py",
    target_id="src/auth/login.py",
    relationship_type="verifies",
    rationale="Tests authentication logic in login module"
)
```

### Pattern C: Impact Analysis Before Refactoring

Before making significant changes:

```
1. BEFORE: impact(file_to_change) to see downstream effects
   - Identify what depends on this file
   - Check which tests cover it
   - Plan updates to affected code

2. MAKE changes

3. AFTER: Verify tests still pass and links are valid
   - Update links if files were renamed
   - Add new links if new dependencies created
```

Example:
```python
# Before refactoring models.py

result = impact("src/trace_core/models.py")
# Output: Shows events.py, graph.py, queries.py, server.py are affected

# Now you know to check these files after refactoring
```

### Pattern D: Design Decision

When documenting a significant design choice:

```
1. CREATE/UPDATE decision doc in docs/

2. REGISTER: add_artifact(doc_path, "decision", doc_path)

3. LINK to affected code: propose_link(decision, code, "implements", "rationale")
   - Rationale: "Decision specifies [aspect] implemented by [code]"
```

Example:
```python
# After creating docs/design_decisions_2025-02-01.md

add_artifact(
    artifact_id="docs/design_decisions_2025-02-01.md",
    artifact_type="decision",
    file_path="docs/design_decisions_2025-02-01.md"
)

propose_link(
    source_id="docs/design_decisions_2025-02-01.md",
    target_id="src/trace_core/models.py",
    relationship_type="implements",
    rationale="Data model decisions implemented in models.py"
)
```

### Pattern E: Dependency Discovery

When you notice a file depends on another (imports, uses, calls):

```
propose_link(
    source_id="file_that_depends",
    target_id="file_depended_on",
    relationship_type="depends_on",
    rationale="[File A] uses [specific functionality] from [File B]"
)
```

Example:
```python
# graph.py imports EventLog from events.py

propose_link(
    source_id="src/trace_core/graph.py",
    target_id="src/trace_core/events.py",
    relationship_type="depends_on",
    rationale="TraceGraph uses EventLog to rebuild graph from events"
)
```

## Relationship Types

Available relationship types:

- **implements** - Code implements requirement/decision
- **depends_on** - File/module depends on another
- **verifies** - Test verifies code/requirement
- **supersedes** - New decision supersedes old
- **contains** - Parent contains child (modules, functions)
- **references** - Generic reference between artifacts

## Don't Over-Capture

**SKIP traceability for:**
- Minor edits (typos, formatting, whitespace)
- Comment-only changes
- Documentation updates that don't affect architecture
- Temporary files or scratch work
- Files outside the repository
- Configuration changes that don't introduce new artifacts

**FOCUS on:**
- New files (src/, tests/, docs/)
- Structural changes (new classes, functions, modules)
- New relationships (imports, dependencies, test coverage)
- Design decisions that affect implementation
- Requirement → implementation links

## Batch Approval Workflow

All AI-generated artifacts and links start in **proposed** state. They need human approval to become **authoritative**.

**During work:**
- Capture freely with `add_artifact` and `propose_link`
- All items are in "proposed" state
- No friction, fast capture

**End of session:**
- Remind user: "X proposed links await approval"
- Suggest: `proposed_links()` to review
- Human runs `accept_proposal(source, target)` to promote

**Example end-of-session message:**
```
✓ Created 3 new artifacts and proposed 5 links.
  Proposed links await approval. To review:
  - Use MCP tool: proposed_links()
  - Accept with: accept_proposal(source_id, target_id)
```

## Query Before Acting

**Use queries to avoid redundant work:**

```python
# Check if artifact already exists
trace("src/new_module.py")  # Returns error if not found

# See what's already linked
trace("src/existing.py")  # Shows upstream/downstream

# Find unlinked artifacts
orphans()  # Shows artifacts with no relationships

# Review pending work
proposed_links()  # Shows what needs approval
```

## Examples in Context

### Example 1: User asks "Add authentication to the API"

```
1. Check context:
   trace("docs/requirements.md")  # See if auth requirement exists

2. Create implementation:
   # Write src/api/auth.py

3. Register:
   add_artifact(
       artifact_id="src/api/auth.py",
       artifact_type="module",
       file_path="src/api/auth.py"
   )

4. Link to requirement:
   propose_link(
       source_id="docs/requirements.md#auth",
       target_id="src/api/auth.py",
       relationship_type="implements",
       rationale="Implements authentication requirement"
   )

5. Create test:
   # Write tests/test_auth.py

   add_artifact(
       artifact_id="tests/test_auth.py",
       artifact_type="test",
       file_path="tests/test_auth.py"
   )

6. Link test to code:
   propose_link(
       source_id="tests/test_auth.py",
       target_id="src/api/auth.py",
       relationship_type="verifies",
       rationale="Tests authentication functionality"
   )

7. End session reminder:
   "✓ Created 2 artifacts, proposed 2 links. Use proposed_links() to review."
```

### Example 2: User asks "Refactor the event log"

```
1. Impact check FIRST:
   impact("src/trace_core/events.py")
   # Shows: graph.py, queries.py depend on this
   # Shows: test_events.py tests this

2. Make changes to events.py

3. Verify tests:
   # Run test_events.py
   # Links automatically stay valid (no file rename)

4. If you add new dependencies:
   propose_link(
       source_id="src/trace_core/events.py",
       target_id="src/trace_core/new_helper.py",
       relationship_type="depends_on",
       rationale="Uses new_helper for event validation"
   )
```

### Example 3: User asks "Document why we chose NetworkX"

```
1. Create/update decision doc:
   # Edit docs/design_decisions_2025-02-01.md

2. Register decision:
   add_artifact(
       artifact_id="docs/design_decisions_2025-02-01.md",
       artifact_type="decision",
       file_path="docs/design_decisions_2025-02-01.md"
   )

3. Link to implementation:
   propose_link(
       source_id="docs/design_decisions_2025-02-01.md",
       target_id="src/trace_core/graph.py",
       relationship_type="implements",
       rationale="NetworkX decision implemented in TraceGraph"
   )
```

## Tool Reference

### Available MCP Tools

All tools are available through the MCP server. Use them naturally in conversation:

**Read-only queries:**
- `trace(artifact_id)` - Get upstream/downstream neighbors
- `impact(artifact_id)` - See all downstream (what breaks if changed)
- `orphans()` - Find unlinked artifacts
- `decisions()` - Get all decision records
- `proposed_links()` - See links awaiting approval

**Write operations:**
- `add_artifact(artifact_id, artifact_type, file_path?, line_start?, content_hash?)` - Register artifact
- `propose_link(source_id, target_id, relationship_type, rationale)` - Create proposed link
- `accept_proposal(source_id, target_id)` - Promote to authoritative (human only)

## Best Practices

1. **Capture as you go** - Don't wait until the end
2. **Be specific in rationales** - "Implements authentication" not just "implements requirement"
3. **Use relative paths** - "src/foo.py" not "/Users/me/project/src/foo.py"
4. **Check impact before refactoring** - Prevents breaking changes
5. **Link tests to code** - Maintain test coverage visibility
6. **Don't capture trivial changes** - Focus on structural relationships
7. **Remind about approvals** - End sessions with pending count

## Anti-Patterns

❌ **Don't:**
- Create artifacts for external libraries (only repo files)
- Link to non-existent artifacts (check with `trace` first)
- Use absolute paths as IDs
- Capture formatting changes
- Forget to check `impact()` before major refactors
- Skip linking tests to code
- Create duplicate artifacts (check if exists first)

✓ **Do:**
- Use file paths as artifact IDs
- Propose links as relationships become clear
- Check impact before breaking changes
- Link every test to its code
- Provide specific, informative rationales
- Batch proposals, approve at natural breakpoints

## Success Criteria

After using this skill, the repository should have:
- ✓ All significant files registered as artifacts
- ✓ Tests linked to code they verify
- ✓ Requirements linked to implementations
- ✓ Dependencies mapped (DEPENDS_ON links)
- ✓ Design decisions linked to implementations
- ✓ No orphans (except standalone docs)
- ✓ Proposed links ready for human approval

## MCP Server Status

The MCP server (`trace-mcp`) must be running to use traceability tools. If tools aren't available:
1. Check if MCP server is configured in Claude Desktop
2. Verify `.trace/` directory exists
3. See `mcp_server/README.md` for setup

---

**Remember:** Traceability is about capturing relationships as you work, not documenting after the fact. The graph builds naturally through normal development.
