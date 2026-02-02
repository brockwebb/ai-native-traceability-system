# Derived Requirements: Artifact Lifecycle & Change Detection

**Parent:** SRS Section [TBD] - System Awareness / Currency
**Status:** Draft
**Date:** 2025-02-02

## Scope

Requirements governing how the trace system maintains awareness of filesystem state and synchronizes with project changes.

## Requirements

### REQ-ALC-001: Respect .gitignore
**Statement:** The system SHALL NOT register artifacts for files matching patterns in .gitignore.

**Rationale:** Ignored files (tmp/, build artifacts, caches) are not project artifacts. Registering them creates noise and stale references.

**Verification:** Test bootstrap scan against repo with .gitignore; verify no ignored files registered.

---

### REQ-ALC-002: Git as File State Source
**Statement:** The system SHALL use git to determine which files exist in the project.

**Rationale:** Git-tracked files are the canonical project state. Untracked files may be temporary or user-specific.

**Verification:** Bootstrap scan uses `git ls-files` or equivalent; verify only tracked files registered.

---

### REQ-ALC-003: File Deletion Detection
**Statement:** The system SHALL detect when a traced artifact's file no longer exists in git.

**Rationale:** Stale references erode trust in the trace graph.

**Verification:** Delete a tracked file, run sync; verify artifact flagged as stale/orphaned.

---

### REQ-ALC-004: File Rename/Move Detection
**Statement:** The system SHALL detect when a traced artifact's file has been moved or renamed, using git rename detection.

**Rationale:** Renamed files should update artifact paths, not create orphans + duplicates.

**Verification:** Rename file with `git mv`, run sync; verify artifact path updated.

---

### REQ-ALC-005: Template-Based Classification
**Statement:** The system SHALL classify artifacts by type using methodology template file_patterns during registration.

**Rationale:** Correct artifact types enable template relationship scaffolding.

**Verification:** Register file matching template pattern; verify artifact_type matches template definition.

---

### REQ-ALC-006: MCP Parity
**Statement:** All artifact lifecycle functionality SHALL be accessible through MCP tools.

**Rationale:** MCP is the capability floor. CC enhances but doesn't replace.

**Verification:** Each capability has corresponding MCP tool; verify via tool list.

---

## Open Questions

1. Archive vs hard-delete for removed artifacts?
2. Confidence threshold for rename detection (git similarity)?
3. Behavior for untracked files explicitly registered?

## Verification Status

| Requirement | Status | Implementation | Verification |
|-------------|--------|----------------|--------------|
| REQ-ALC-001 | ✅ PASS | scripts/bootstrap_scan.py:get_git_tracked_files() | No tmp/ files registered (0/43) |
| REQ-ALC-002 | ✅ PASS | scripts/bootstrap_scan.py:get_git_tracked_files() | Only git-tracked files (43/52 tracked) |
| REQ-ALC-003 | ⏸️ DEFERRED | src/trace_core/git_sync.py (stub) | Future: v0.2 |
| REQ-ALC-004 | ⏸️ DEFERRED | src/trace_core/git_sync.py (stub) | Future: v0.2 |
| REQ-ALC-005 | ✅ PASS | scripts/bootstrap_scan.py:classify_file() | Correct types: architecture(1), conops(1), requirement(1), decision(1), design(1), test(7), module(17) |
| REQ-ALC-006 | ✅ PASS | mcp_server/server.py | MCP tools: list_templates, get_template, apply_template, classify_artifact |

**Test Suite:** tests/test_artifact_lifecycle.py (4/4 tests passing)

**Last Verified:** 2025-02-02

## Trace Links

- Implements: [SRS currency/awareness section - TBD]
- Verified by: tests/test_artifact_lifecycle.py
