# Common Workflows

## Starting a New Project

```bash
# 1. Initialize
cd my-project
trace init

# 2. Bootstrap (if existing code)
# trace init runs bootstrap_scan automatically

# 3. Review proposed artifacts
# Use Claude: "Show me proposed artifacts"

# 4. Approve in batches
# Use Claude: "Accept all proposed links"
```

## Adding a New Feature

1. **Create requirement** (if formal project)
   - Add to `docs/requirements/`
   - CC registers automatically

2. **Write code**
   - CC registers new files
   - CC infers dependencies from imports

3. **Write tests**
   - CC links tests to code via `verifies`

4. **Review and approve**
   - "Show me proposed links"
   - "Accept all proposed"

## Before Modifying Code

Ask Claude: "What depends on auth_module?"

Or let the skill file handle it - CC checks impact automatically and warns if >3 downstream dependencies.

## Recording Decisions

Tell Claude: "Log decision: We chose PostgreSQL over MongoDB because we need ACID transactions for financial data."

CC creates a decision artifact with rationale, links to relevant requirements.

## Finding Things

```
"List all requirements"
"Search for auth-related artifacts"
"Show me orphan tests"
"What decisions did we make this week?"
```

## Health Checks

```
"Run health check"
```

Reports:
- Missing files (traced but deleted)
- Broken links
- Stale data

## Syncing with Git

```
"Sync trace with git"
```

Detects:
- New files (in git, not traced)
- Deleted files (traced, not in git)
- Renames
