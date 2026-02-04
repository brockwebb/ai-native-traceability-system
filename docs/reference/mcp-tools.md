# MCP Tools Reference

22 tools organized by function.

## Query Tools

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

## Discovery Tools

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

## Write Tools

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

## Approval Tools

### accept_proposal
Promote single link to authoritative.

**Input:** `source_id`, `target_id`
**Output:** `{success, source, target, state: "authoritative"}`

### accept_all_proposed
Promote all pending links.

**Input:** none
**Output:** `{promoted_links[], count}`

### accept_by_type
Promote all links of a relationship type.

**Input:** `relationship_type`
**Output:** `{promoted_links[], count}`

### accept_by_source
Promote all links from a source artifact.

**Input:** `artifact_id`
**Output:** `{promoted_links[], count}`

---

## Template Tools

### list_templates
List available methodology templates.

**Input:** none
**Output:** `{templates[], count}`

### get_template
Get template definition.

**Input:** `name`
**Output:** `{template: {name, artifact_types, relationship_chains, ...}}`

### apply_template
Scaffold relationships from template.

**Input:** `name`
**Output:** `{template, proposed_links[], count}`

### classify_artifact
Suggest artifact type for a file.

**Input:**
- `file_path` (required)
- `template` (optional)

**Output:** `{file_path, suggested_type, template_used}`

---

## Maintenance Tools

### health_check
Validate trace data integrity.

**Input:** none
**Output:** `{issues[], healthy: bool}`

Checks:
- Missing files (traced but not on disk)
- Broken links (references non-existent artifacts)
- Invalid artifact types

### sync_with_git
Synchronize with git repository state.

**Input:** none
**Output:** `{added[], deleted[], renamed[]}`

Detects:
- Files in git but not traced
- Traced files not in git
- File renames

---

## Automation Tools (v0.3)

### register_file
Auto-classify and register a file.

**Input:** `file_path`
**Output:** `{artifact_id, artifact_type, success, already_exists}`

Use immediately after creating files. Idempotent.

### check_impact
Check downstream impact before modification.

**Input:**
- `artifact_id` (required)
- `threshold` (optional, default: 3)

**Output:** `{downstream[], count, exceeds_threshold, warning}`

### infer_dependencies
Analyze imports and propose depends_on links.

**Input:**
- `file_path` (required)
- `auto_propose` (optional, default: false)

**Output:** `{file_path, dependencies[], proposed_count}`

Parses:
- Python imports
- Markdown links
