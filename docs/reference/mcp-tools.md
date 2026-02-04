# MCP Tools Reference

28 tools organized by category.

## Query Tools (5)

### trace
Get immediate neighbors of an artifact.

**Input:** `artifact_id` (string)
**Output:** `{artifact_id, upstream[], downstream[]}`

```json
{"artifact_id": "auth.py"}
→ {"artifact_id": "auth.py", "upstream": ["REQ-1"], "downstream": ["test_auth.py"]}
```

### impact
Get all artifacts affected if this changes (transitive downstream).

**Input:** `artifact_id` (string)
**Output:** `{artifact_id, affected_artifacts[], count}`

### orphans
Find artifacts with no relationships.

**Input:** none
**Output:** `{orphan_artifacts[], count}`

### decisions
Get all decision records.

**Input:** none
**Output:** `{decisions[], count}`

### proposed_links
Get links awaiting approval.

**Input:** none
**Output:** `{proposed_links[], count}`

---

## Discovery Tools (2)

### list_artifacts
List all registered artifacts.

**Input:** `artifact_type` (optional filter)
**Output:** `{artifacts: [{artifact_id, artifact_type, file_path, tags}], count}`

### search_artifacts
Search by name, path, type, or tags.

**Input:**
- `query` - Substring search in IDs and paths
- `artifact_type` - Type filter
- `tags` - Array of tags (OR match)

**Output:** `{matches[], count}`

---

## Write Tools (2)

### add_artifact
Register a new artifact.

**Input:**
- `artifact_id` (required)
- `artifact_type` (required)
- `file_path` (optional)
- `line_start` (optional)
- `content_hash` (optional)
- `tags` (optional array)

**Output:** `{success, artifact_id, state: "proposed"}`

### propose_link
Create a relationship between artifacts.

**Input:**
- `source_id` (required)
- `target_id` (required)
- `relationship_type` (required)
- `rationale` (required)

**Output:** `{success, source, target, relationship_type, state: "proposed"}`

---

## Approval Tools (4)

### accept_proposal
Promote single link to authoritative.

**Input:** `source_id`, `target_id`
**Output:** `{success, source, target, state: "authoritative"}`

### accept_all_proposed
Batch promote all proposed links.

**Input:** none
**Output:** `{promoted_count, results[]}`

### accept_by_type
Promote all links of specific relationship type.

**Input:** `relationship_type` (e.g., "implements", "verifies")
**Output:** `{promoted_count, relationship_type}`

### accept_by_source
Promote all links from specific artifact.

**Input:** `artifact_id`
**Output:** `{promoted_count, source_id}`

---

## Template Tools (4)

### list_templates
Get available methodology templates.

**Input:** none
**Output:** `{templates: [{name, description}], count}`

### get_template
Get template details.

**Input:** `name` (e.g., "agile", "systems-engineering")
**Output:** `{template: {name, description, artifact_types, relationship_chains}}`

### apply_template
Scaffold artifacts and relationships from template.

**Input:** `name`
**Output:** `{template, proposed_links[], count}`

### classify_artifact
Suggest artifact type based on file path.

**Input:**
- `file_path` (required)
- `template` (optional)

**Output:** `{file_path, suggested_type, template_used}`

---

## Maintenance Tools (2)

### health_check
Validate trace data integrity.

**Input:** none
**Output:**
```json
{
  "status": "healthy|warnings",
  "stats": {
    "artifact_count": 42,
    "link_count": 67,
    "proposed_count": 5
  },
  "issues": [
    {"type": "missing_file", "artifacts": [...]}
  ]
}
```

### sync_with_git
Detect file changes and propose status updates.

**Input:** none
**Output:**
```json
{
  "git_files": [...],
  "traced_artifacts": [...],
  "missing_files": [...],
  "untraced_files": [...]
}
```

---

## Automation Tools (3) - v0.3

### register_file
Auto-classify and register a file. Use immediately after creating any new file.

**Input:** `file_path` (required)
**Output:**
```json
{
  "success": true,
  "artifact_id": "src/auth.py",
  "artifact_type": "module",
  "state": "proposed"
}
```

**Usage:** Claude Code calls this automatically via skill file.

### check_impact
Check downstream impact before modifying a file. Warns if dependencies exceed threshold.

**Input:**
- `artifact_id` (required)
- `threshold` (optional, default: 3)

**Output:**
```json
{
  "artifact_id": "auth.py",
  "downstream_count": 7,
  "exceeds_threshold": true,
  "warning": "High impact change",
  "affected": ["test_auth.py", "login.py", ...]
}
```

**Usage:** Claude Code calls this before modifications via skill file.

### infer_dependencies
Analyze a file's imports/references and propose depends_on links to traced artifacts.

**Input:**
- `file_path` (required)
- `auto_propose` (optional, default: false)

**Output:**
```json
{
  "file_path": "src/api.py",
  "dependencies_found": ["auth", "database"],
  "proposed_links": [
    {"source": "src/api.py", "target": "src/auth.py", "type": "depends_on"}
  ]
}
```

**Usage:** Claude Code calls this after file creation/modification via skill file.

---

## Report Tools (6) - v0.4

### export_mermaid
Export graph subset as Mermaid flowchart diagram.

**Input:**
- `root` (optional) - Root artifact to start from
- `depth` (optional) - Max traversal depth
- `direction` (optional) - "upstream", "downstream", or "both" (default)
- `artifact_types` (optional) - Filter array
- `relationship_types` (optional) - Filter array

**Output:**
```json
{
  "format": "mermaid",
  "diagram": "flowchart TD\n    subgraph modules\n..."
}
```

**Usage:**
```
"Generate a mermaid diagram for the auth module"
"Show me dependency graph for requirements only"
```

### export_dependency_map
Export dependency map in various formats for visualization.

**Input:**
- `root` (optional) - Root artifact
- `depth` (optional) - Max depth
- `format` (optional) - "mermaid" (default), "dot", or "json"
- `artifact_types` (optional) - Filter array
- `relationship_types` (optional) - Filter array

**Output:**
```json
{
  "format": "dot",
  "output": "digraph G {\n  rankdir=TB;\n..."
}
```

**Formats:**
- `mermaid` - Flowchart syntax
- `dot` - Graphviz syntax
- `json` - Structured data with nodes[] and edges[]

### export_coverage_report
Generate coverage report showing traceability gaps.

**Input:**
- `format` (optional) - "md" (default) or "json"

**Output:**
```json
{
  "format": "md",
  "report": "# Coverage Report\n\n## Summary\n- Requirements: 2/10 orphaned..."
}
```

**Identifies:**
- Orphan requirements (no implementation)
- Untested modules (no verifies)
- Undocumented decisions (no links)
- Pending approvals count

**Usage:**
```
"Show me coverage gaps"
"What requirements are orphaned?"
```

### export_rtm
Generate Requirements Traceability Matrix.

**Input:**
- `format` (optional) - "md" (default), "csv", or "json"

**Output:**
```json
{
  "format": "md",
  "rtm": "# Requirements Traceability Matrix\n\n| Requirement | Implementations | Tests | Status |\n..."
}
```

**Statuses:**
- ✅ Fully Traced - Has implementations and tests
- ⚠️ Untested - Has implementations, no tests
- ⚠️ No Implementation - Has tests, no implementation
- ❌ Orphan - No implementations or tests

**Usage:**
```
"Generate an RTM"
"Show me requirements traceability as CSV"
```

### export_impact_report
Generate impact analysis report with risk assessment.

**Input:**
- `artifact_ids` (required) - Array of artifacts to analyze
- `format` (optional) - "md" (default) or "json"

**Output:**
```json
{
  "format": "md",
  "report": "# Impact Report\n\n**Risk Level:** High\n...",
  "artifacts_analyzed": 2
}
```

**Risk Levels:**
- 🔴 High - More than 10 affected artifacts
- 🟡 Medium - 3-10 affected artifacts
- 🟢 Low - Fewer than 3 affected artifacts

**Shows:**
- Direct dependents (1 hop)
- Transitive dependents (full cascade)
- Affected artifacts grouped by type

**Usage:**
```
"What's affected if I change auth.py?"
"Impact report for the database module"
```

### export_decision_log
Generate chronological decision log.

**Input:**
- `since` (optional) - Date filter string
- `format` (optional) - "md" (default) or "json"

**Output:**
```json
{
  "format": "md",
  "log": "# Decision Log\n\n## DEC-001-database-choice\n..."
}
```

**Includes:**
- Decision ID
- File path
- Status (proposed/authoritative)
- Tags
- Sorted chronologically by ID

**Usage:**
```
"Show me all decisions"
"What decisions did we make in January?"
```

---

## Tool Categories Summary

| Category | Count | Tools |
|----------|-------|-------|
| Query | 5 | trace, impact, orphans, decisions, proposed_links |
| Discovery | 2 | list_artifacts, search_artifacts |
| Write | 2 | add_artifact, propose_link |
| Approval | 4 | accept_proposal, accept_all_proposed, accept_by_type, accept_by_source |
| Template | 4 | list_templates, get_template, apply_template, classify_artifact |
| Maintenance | 2 | health_check, sync_with_git |
| Automation | 3 | register_file, check_impact, infer_dependencies |
| Reports | 6 | export_mermaid, export_dependency_map, export_coverage_report, export_rtm, export_impact_report, export_decision_log |

**Total: 28 tools**
