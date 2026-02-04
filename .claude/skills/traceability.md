# Traceability Skill

**MANDATORY BEHAVIORS** for maintaining project memory that survives context windows.

**Philosophy:** The system documents itself confidently. Human intervention is for decisions and corrections, not routine approval.

---

## RULE 1: ALWAYS Register New Files

**Trigger:** Immediately after creating ANY file in `src/`, `tests/`, `docs/`, or `scripts/`

**Action:** Call `register_file()` (preferred) or `add_artifact()` before doing anything else.

```python
# IMMEDIATELY after creating a file:
register_file(file_path="<relative_path>")  # Auto-classifies type

# Or manually:
add_artifact(
    artifact_id="<relative_path>",
    artifact_type="<type>",
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

**Action:** Call `check_impact()` - warns if downstream count > threshold

```python
# BEFORE editing an existing file:
result = check_impact(artifact_id="<file_path>", threshold=3)

# If exceeds_threshold is true, WARN THE USER:
# "⚠️ This file has N downstream dependencies: [list]. Proceed?"
# WAIT for human decision before proceeding.
```

**This is the human-in-the-loop point.** High-impact changes require explicit human approval. This decision is traced.

**Skip impact check for:**
- New files (not yet in graph)
- Files in `handoffs/`, `cc_tasks/`
- Config files (`.gitignore`, `pyproject.toml`)

---

## RULE 3: ALWAYS Link Tests to Code

**Trigger:** After creating a test file

**Action:** Create `verifies` link to the code under test

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

**Action:** Create `implements` link

```python
propose_link(
    source_id="<implementation_file>",
    target_id="<requirement_doc>",
    relationship_type="implements",
    rationale="Implements <REQ-ID>: <description>"
)
```

---

## RULE 5: ALWAYS Infer Dependencies

**Trigger:** After creating or significantly modifying a Python or Markdown file

**Action:** Run dependency inference

```python
infer_dependencies(file_path="<relative_path>", auto_propose=True)
```

---

## RULE 6: ALWAYS Auto-Accept at Session End

**Trigger:** End of conversation or task completion

**Action:** Accept all proposed links and provide summary

```python
# At session end:
accept_all_proposed()
```

**Rationale:** The system documents itself confidently. Routine graph maintenance should not require human approval. Human reviews outputs (RTM, coverage reports) and corrects if needed.

**Session summary:**
```
✓ Traceability summary:
  - Artifacts registered: N
  - Links created: N
  - Graph health: [healthy/issues]
```

---

## Human Intervention Points

The system runs autonomously EXCEPT:

1. **High-impact warnings** - When `check_impact()` exceeds threshold, STOP and ask
2. **Ambiguity** - When unsure how to classify or link, ASK for direction
3. **Report review** - Human reviews RTM/coverage and may request corrections
4. **Explicit override** - Human says "don't link X" or "this should be type Y"

All human decisions at these points are traced.

---

## Quick Reference

### MCP Tools

| Tool | Use |
|------|-----|
| `register_file(file_path)` | Auto-classify and register |
| `add_artifact(id, type, file_path)` | Manual registration |
| `propose_link(source, target, rel_type, rationale)` | Create relationship |
| `accept_all_proposed()` | Batch approve (session end) |
| `check_impact(artifact_id, threshold)` | Pre-modification warning |
| `infer_dependencies(file_path, auto_propose)` | Parse imports |
| `trace(artifact_id)` | See neighbors |
| `health_check()` | Validate graph integrity |

### Report Tools (Human-Facing)

| Tool | Use |
|------|-----|
| `export_mermaid(...)` | Dependency visualization |
| `export_rtm(format)` | Requirements traceability matrix |
| `export_coverage_report(format)` | Gap analysis |
| `export_impact_report(artifact_ids, format)` | Change blast radius |
| `export_decision_log(since, format)` | Decision history |

### Relationship Types

| Type | Meaning |
|------|---------|
| `implements` | Code implements requirement/decision |
| `verifies` | Test verifies code |
| `depends_on` | File depends on another |
| `documents` | Doc describes implementation |
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

- [ ] All new files registered with `register_file()`
- [ ] Tests linked to code with `verifies`
- [ ] Implementations linked to requirements with `implements`
- [ ] Dependencies inferred with `infer_dependencies()`
- [ ] Impact checked before modifying existing traced files
- [ ] All proposed links accepted with `accept_all_proposed()`
- [ ] Session summary provided
