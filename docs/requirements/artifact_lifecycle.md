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

## Trace Links

- Implements: [SRS currency/awareness section - TBD]
- Verified by: tests/test_artifact_lifecycle.py [to be created]
