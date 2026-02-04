# Automatic Capture

These features work invisibly via the Claude Code skill file. You don't ask for them—they just happen.

## How It Works

The skill file (`.claude/skills/traceability.md`) contains 5 mandatory rules that Claude Code follows:

### Rule 1: Register New Files

**Trigger:** CC creates any file
**Action:** Immediately calls `register_file(path)`
**Result:** File becomes a traced artifact with auto-detected type

You'll never see this happen. Check with:
```
"List all registered artifacts"
```

### Rule 2: Check Impact Before Modifications

**Trigger:** CC is about to modify a file
**Action:** Calls `check_impact(artifact_id, threshold=3)`
**Result:** Warning if >3 downstream dependencies

You'll see a warning like:
> ⚠️ This artifact has 7 downstream dependencies. Modifying it may affect: test_auth.py, login.py, ...

### Rule 3: Link Tests to Code

**Trigger:** CC creates a test file
**Action:** Proposes `verifies` link to tested module
**Result:** Test → Module relationship captured

### Rule 4: Link Implementations to Requirements

**Trigger:** CC implements something from requirements
**Action:** Proposes `implements` link
**Result:** Code → Requirement relationship captured

### Rule 5: Infer Dependencies

**Trigger:** CC analyzes a Python/Markdown file
**Action:** Parses imports, proposes `depends_on` links
**Result:** Module → Module dependencies captured

## Authority Model

All automatic captures are **proposed**, not authoritative. You approve them:

```
"Show me proposed links"
"Accept all proposed"
```

Or selectively:
```
"Accept all implements links"
"Accept links from auth.py"
```

## Checking What Was Captured

Even though it's invisible, you can always inspect:

```
"What depends on auth_module?"     → trace tool
"Show me orphan artifacts"         → orphans tool
"Run health check"                 → health_check tool
"Sync with git"                    → sync_with_git tool
```

## Tuning Automatic Behavior

Edit `.claude/skills/traceability.md` to:
- Change impact threshold (default: 3)
- Add/remove rules
- Customize artifact type mappings
