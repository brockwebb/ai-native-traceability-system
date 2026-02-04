# Traceability Skill

**MANDATORY BEHAVIORS** for maintaining project memory that survives context windows.

---

## RULE 1: ALWAYS Register New Files

**Trigger:** Immediately after creating ANY file in `src/`, `tests/`, `docs/`, or `scripts/`

**Action:** Call `add_artifact()` before doing anything else.

```python
# IMMEDIATELY after creating a file:
add_artifact(
    artifact_id="<relative_path>",      # e.g., "src/auth/login.py"
    artifact_type="<type>",             # see type mapping below
    file_path="<relative_path>"
)
```

**Type Mapping:**
| Path Pattern | Type |
|--------------|------|
| `src/**/*.py` | module |
| `tests/**/*.py` | test |
| `docs/decisions/**` | decision |
| `docs/requirements/**` | requirement |
| `docs/architecture/**` | architecture |
| `docs/**/*.md` | document |
| `scripts/**/*.py` | module |
| `*.md` (root) | document |

**No exceptions.** Every new file gets registered.

---

## RULE 2: ALWAYS Check Impact Before Modifying

**Trigger:** Before modifying any file that might be in the trace graph

**Action:** Call `impact()` and warn if downstream count > 3

```python
# BEFORE editing an existing file:
result = impact("<file_path>")

# If result shows downstream artifacts, WARN THE USER:
# "⚠️ This file has N downstream dependencies: [list]. Proceed?"
```

**Impact threshold:** If downstream count > 3, STOP and warn before proceeding.

**Skip impact check for:**
- New files (not yet in graph)
- Files in `handoffs/`, `cc_tasks/`
- Config files (`.gitignore`, `pyproject.toml`)

---

## RULE 3: ALWAYS Link Tests to Code

**Trigger:** After creating a test file

**Action:** Propose `verifies` link to the code under test

```python
# After registering test file:
propose_link(
    source_id="tests/test_foo.py",
    target_id="src/module/foo.py",
    relationship_type="verifies",
    rationale="Tests <specific functionality>"
)
```

---

## RULE 4: ALWAYS Link Implementations to Requirements

**Trigger:** After implementing something from a requirement

**Action:** Propose `implements` link

```python
propose_link(
    source_id="<requirement_doc>",
    target_id="<implementation_file>",
    relationship_type="implements",
    rationale="Implements <REQ-ID>: <description>"
)
```

---

## RULE 5: ALWAYS Summarize at Session End

**Trigger:** End of conversation or task completion

**Action:** Report traceability activity

```
✓ Traceability summary:
  - Artifacts registered: N
  - Links proposed: N
  - Pending approvals: N (use `proposed_links()` to review)
```

---

## Quick Reference

### MCP Tools

| Tool | Use |
|------|-----|
| `add_artifact(id, type, file_path)` | Register new file |
| `propose_link(source, target, rel_type, rationale)` | Create relationship |
| `impact(artifact_id)` | Check downstream before editing |
| `trace(artifact_id)` | See neighbors |
| `proposed_links()` | Review pending |
| `health_check()` | Validate graph integrity |

### Relationship Types

| Type | Meaning |
|------|---------|
| `implements` | Code implements requirement/decision |
| `verifies` | Test verifies code |
| `depends_on` | File depends on another |
| `references` | Generic reference |
| `supersedes` | Replaces older artifact |

### Artifact ID Convention

**ALWAYS use relative paths:**
- ✓ `src/trace_core/models.py`
- ✓ `tests/test_events.py`
- ✗ `/Users/brock/.../models.py`
- ✗ `models` or `test_events`

---

## DO NOT Capture

- Typo fixes, formatting, whitespace
- Comment-only changes
- Files in `handoffs/`, `cc_tasks/`
- External dependencies
- Temporary/scratch files

---

## Checklist

Before ending any task, verify:

- [ ] All new files registered with `add_artifact()`
- [ ] Tests linked to code with `verifies`
- [ ] Implementations linked to requirements with `implements`
- [ ] Impact checked before modifying existing traced files
- [ ] Session summary provided with pending approval count
