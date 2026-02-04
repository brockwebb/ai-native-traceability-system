# Skill File Test Battery

**Purpose:** Verify CC follows the traceability skill rules.
**Date:** 2025-02-03
**Requirements:** REQ-AUTO-001, REQ-IMPACT-001, REQ-SKILL-001

---

## Test Protocol

For each test:
1. Start fresh CC session in this repo
2. Give CC the task prompt
3. Observe behavior
4. Record pass/fail and notes

---

## TEST-AUTO-001: New Module Registration

**Task prompt:**
> "Create a new file `src/trace_core/validators.py` with a function `validate_artifact_id(id: str) -> bool` that checks if an ID follows our conventions."

**Expected behavior:**
1. CC creates the file
2. CC IMMEDIATELY calls `add_artifact("src/trace_core/validators.py", "module", "src/trace_core/validators.py")`
3. Does NOT wait until end of task

**Pass criteria:**
- [ ] `add_artifact()` called
- [ ] Called immediately after file creation, not at end
- [ ] Correct artifact_type ("module")

---

## TEST-AUTO-002: New Test Registration + Link

**Task prompt:**
> "Create a test file `tests/test_validators.py` that tests the `validate_artifact_id` function."

**Prerequisite:** TEST-AUTO-001 completed (validators.py exists)

**Expected behavior:**
1. CC creates test file
2. CC calls `add_artifact("tests/test_validators.py", "test", "tests/test_validators.py")`
3. CC calls `propose_link("tests/test_validators.py", "src/trace_core/validators.py", "verifies", "...")`

**Pass criteria:**
- [ ] Test file registered as artifact
- [ ] `verifies` link proposed to validators.py
- [ ] Rationale is specific (not generic)

---

## TEST-AUTO-003: New Doc Registration

**Task prompt:**
> "Create a design decision document at `docs/decisions/dd_validation_rules.md` explaining our artifact ID validation approach."

**Expected behavior:**
1. CC creates the doc
2. CC calls `add_artifact("docs/decisions/dd_validation_rules.md", "decision", "...")`
3. Optionally proposes link to validators.py

**Pass criteria:**
- [ ] Document registered as artifact
- [ ] Correct type ("decision")

---

## TEST-IMPACT-001: Impact Check Before Edit

**Task prompt:**
> "Refactor `src/trace_core/models.py` to add a new field `metadata: dict` to the Event class."

**Expected behavior:**
1. CC calls `impact("src/trace_core/models.py")` FIRST
2. CC reports downstream dependencies to user
3. CC asks for confirmation or warns before proceeding
4. Only then makes the edit

**Pass criteria:**
- [ ] `impact()` called BEFORE any edits
- [ ] User warned about downstream effects
- [ ] Did NOT silently edit without impact check

---

## TEST-IMPACT-002: Skip Impact for New Files

**Task prompt:**
> "Create a new utility file `src/trace_core/utils.py` with a helper function."

**Expected behavior:**
1. CC creates file
2. CC registers artifact
3. CC does NOT call `impact()` (file is new, not in graph)

**Pass criteria:**
- [ ] No unnecessary `impact()` call
- [ ] File still registered

---

## TEST-IMPACT-003: Skip Impact for Excluded Paths

**Task prompt:**
> "Update the handoff file `handoffs/2025-02-02_mvp_complete_v02_ready.md` to mark v0.2 as complete."

**Expected behavior:**
1. CC edits the file
2. CC does NOT call `impact()` (handoffs are excluded)
3. CC does NOT register as artifact (handoffs excluded)

**Pass criteria:**
- [ ] No `impact()` call
- [ ] No `add_artifact()` call
- [ ] Edit completed normally

---

## TEST-LINK-001: Requirement Implementation Link

**Task prompt:**
> "Implement REQ-INIT-001 from `docs/requirements/v0.3_requirements.md` by creating the trace init CLI."

**Expected behavior:**
1. CC checks the requirement
2. CC creates implementation files
3. CC registers artifacts
4. CC proposes `implements` link from requirement to implementation

**Pass criteria:**
- [ ] `propose_link()` called with `implements` relationship
- [ ] Source is requirement doc/anchor
- [ ] Target is implementation file
- [ ] Rationale references REQ-INIT-001

---

## TEST-SESSION-001: End of Session Summary

**Task prompt:**
> "Create a simple module `src/trace_core/constants.py` with some constants, then we're done for today."

**Expected behavior:**
1. CC creates file
2. CC registers artifact
3. At end, CC provides summary:
   ```
   ✓ Traceability summary:
     - Artifacts registered: 1
     - Links proposed: 0
     - Pending approvals: N
   ```

**Pass criteria:**
- [ ] Summary provided without prompting
- [ ] Accurate counts
- [ ] Mentions pending approvals

---

## TEST-NOISY-001: Ignores Trivial Changes

**Task prompt:**
> "Fix the typo in line 5 of `src/trace_core/models.py` — change 'teh' to 'the'."

**Expected behavior:**
1. CC makes the fix
2. CC does NOT register new artifact (existing file)
3. CC does NOT propose links (trivial change)
4. May or may not check impact (acceptable either way for typo)

**Pass criteria:**
- [ ] No unnecessary `add_artifact()` call
- [ ] No unnecessary `propose_link()` call

---

## Results Template

| Test ID | Date | Pass/Fail | Notes |
|---------|------|-----------|-------|
| TEST-AUTO-001 | | | |
| TEST-AUTO-002 | | | |
| TEST-AUTO-003 | | | |
| TEST-IMPACT-001 | | | |
| TEST-IMPACT-002 | | | |
| TEST-IMPACT-003 | | | |
| TEST-LINK-001 | | | |
| TEST-SESSION-001 | | | |
| TEST-NOISY-001 | | | |

---

## Iteration Notes

After running tests, update skill file based on failures:
- If CC doesn't follow a rule, make language stronger
- If CC over-applies a rule, add exceptions
- Re-run failed tests after updates
