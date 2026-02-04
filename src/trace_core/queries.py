"""Query functions for the trace graph."""
from typing import Any
import subprocess
from pathlib import Path

import networkx as nx

from .graph import TraceGraph
from .models import State


class TraceQueries:
    """High-level queries against the trace graph."""

    def __init__(self, trace_graph: TraceGraph, template_loader=None):
        self.tg = trace_graph
        self.template_loader = template_loader

    def trace(self, artifact_id: str) -> dict[str, list[str]]:
        """Get upstream and downstream artifacts."""
        return {
            "upstream": self.tg.get_neighbors(artifact_id, "upstream"),
            "downstream": self.tg.get_neighbors(artifact_id, "downstream"),
        }

    def impact(self, artifact_id: str) -> list[str]:
        """Get all artifacts affected if this one changes (transitive downstream)."""
        if artifact_id not in self.tg.graph:
            return []
        return list(nx.descendants(self.tg.graph, artifact_id))

    def orphans(self) -> list[str]:
        """Find artifacts with no incoming or outgoing relationships."""
        return [n for n in self.tg.graph.nodes() if self.tg.graph.degree(n) == 0]

    def proposed_links(self) -> list[tuple[str, str, dict]]:
        """Get all links in proposed state (awaiting approval)."""
        return [
            (u, v, d)
            for u, v, d in self.tg.graph.edges(data=True)
            if d.get("state") == State.PROPOSED.value
        ]

    def by_type(self, artifact_type: str) -> list[str]:
        """Get all artifacts of a given type."""
        return [
            n for n, d in self.tg.graph.nodes(data=True)
            if d.get("artifact_type") == artifact_type
        ]

    def decisions(self) -> list[dict]:
        """Get all decision artifacts."""
        return [
            self.tg.get_artifact(n)
            for n in self.by_type("decision")
            if self.tg.get_artifact(n)
        ]

    def list_artifacts(self, artifact_type: str | None = None) -> list[dict]:
        """List all artifacts, optionally filtered by type."""
        if artifact_type:
            artifact_ids = self.by_type(artifact_type)
        else:
            artifact_ids = list(self.tg.graph.nodes())

        return [
            self.tg.get_artifact(artifact_id)
            for artifact_id in artifact_ids
            if self.tg.get_artifact(artifact_id)
        ]

    def search_artifacts(
        self,
        query: str | None = None,
        artifact_type: str | None = None,
        tags: list[str] | None = None
    ) -> list[dict]:
        """Search artifacts by name, path, type, or tags.

        Args:
            query: Substring to match in artifact_id or file_path
            artifact_type: Filter by artifact type
            tags: List of tags - matches if artifact has ANY of these tags

        Returns:
            List of artifact dicts that match the criteria
        """
        matches = []

        # Start with all artifacts or type-filtered
        if artifact_type:
            candidates = self.by_type(artifact_type)
        else:
            candidates = list(self.tg.graph.nodes())

        for artifact_id in candidates:
            artifact = self.tg.get_artifact(artifact_id)
            if not artifact:
                continue

            # Check query match (substring in ID or file_path)
            if query:
                query_lower = query.lower()
                id_match = query_lower in artifact_id.lower()
                file_path = artifact.get("file_path", "")
                path_match = query_lower in file_path.lower()

                if not (id_match or path_match):
                    continue

            # Check tags match (artifact has ANY of the specified tags)
            if tags:
                artifact_tags = artifact.get("tags", [])
                if not any(tag in artifact_tags for tag in tags):
                    continue

            matches.append(artifact)

        return matches

    def _check_version_alignment(self, repo_root: Path) -> list[dict]:
        """Check pyproject.toml version matches latest git tag.

        Args:
            repo_root: Path to git repo root

        Returns:
            List of issues (empty if aligned or no check needed)
        """
        issues = []

        pyproject_path = repo_root / "pyproject.toml"
        if not pyproject_path.exists():
            return []  # No pyproject.toml, skip check

        # Parse version from pyproject.toml
        try:
            import tomllib
        except ImportError:
            # Python < 3.11, try tomli
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                return []  # Can't parse, skip

        try:
            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)
            pkg_version = pyproject.get("project", {}).get("version")
        except Exception:
            return []  # Can't parse, skip

        if not pkg_version:
            return []

        # Get latest git tag
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return []  # No tags, skip

            latest_tag = result.stdout.strip()

            # Normalize: v0.4.0 -> 0.4.0
            tag_version = latest_tag.lstrip("v")

            if tag_version != pkg_version:
                issues.append({
                    "type": "version_mismatch",
                    "message": f"pyproject.toml version ({pkg_version}) != latest git tag ({latest_tag})",
                    "pyproject_version": pkg_version,
                    "git_tag": latest_tag
                })
        except FileNotFoundError:
            pass  # git not available

        return issues

    def health_check(self, repo_root: Path | None = None) -> dict:
        """Validate trace data integrity.

        Checks:
        - All artifact file_paths exist in git
        - No broken links (source or target artifact missing)
        - No duplicate artifact IDs
        - All artifact_types are valid per loaded templates
        - Events file is parseable (implicit if we loaded successfully)
        - Version alignment (pyproject.toml vs git tag)

        Args:
            repo_root: Path to git repo root (defaults to cwd)

        Returns:
            Dict with validation results
        """
        if repo_root is None:
            repo_root = Path.cwd()

        issues = []
        warnings = []

        # Get git-tracked files
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            git_files = set(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError as e:
            issues.append({
                "type": "git_error",
                "message": f"Failed to get git files: {e}"
            })
            git_files = set()

        # Check 1: All artifact file_paths exist in git
        for artifact_id in self.tg.graph.nodes():
            artifact = self.tg.get_artifact(artifact_id)
            if not artifact:
                continue

            file_path = artifact.get("file_path")
            if file_path:
                if file_path not in git_files:
                    issues.append({
                        "type": "missing_file",
                        "artifact_id": artifact_id,
                        "file_path": file_path,
                        "message": f"File '{file_path}' for artifact '{artifact_id}' not found in git"
                    })

        # Check 2: No broken links (source or target missing)
        # Check if artifacts were properly registered (exist in _artifacts dict)
        # not just as graph nodes (which can be auto-created by edges)
        for u, v, d in self.tg.graph.edges(data=True):
            if self.tg.get_artifact(u) is None:
                issues.append({
                    "type": "broken_link",
                    "source_id": u,
                    "target_id": v,
                    "message": f"Link source '{u}' not registered as artifact"
                })
            if self.tg.get_artifact(v) is None:
                issues.append({
                    "type": "broken_link",
                    "source_id": u,
                    "target_id": v,
                    "message": f"Link target '{v}' not registered as artifact"
                })

        # Check 3: No duplicate artifact IDs
        # (NetworkX graph structure prevents duplicates, but we verify)
        seen_ids = set()
        for artifact_id in self.tg.graph.nodes():
            if artifact_id in seen_ids:
                issues.append({
                    "type": "duplicate_id",
                    "artifact_id": artifact_id,
                    "message": f"Duplicate artifact ID: '{artifact_id}'"
                })
            seen_ids.add(artifact_id)

        # Check 4: All artifact_types are valid per loaded templates
        if self.template_loader:
            valid_types = set()
            for template_name in self.template_loader.list_templates():
                template = self.template_loader.get_template(template_name)
                if template:
                    for atype in template.get("artifact_types", []):
                        valid_types.add(atype["id"])

            for artifact_id in self.tg.graph.nodes():
                artifact = self.tg.get_artifact(artifact_id)
                if not artifact:
                    continue

                artifact_type = artifact.get("artifact_type")
                if artifact_type and artifact_type not in valid_types:
                    warnings.append({
                        "type": "unknown_artifact_type",
                        "artifact_id": artifact_id,
                        "artifact_type": artifact_type,
                        "message": f"Artifact type '{artifact_type}' not found in any template"
                    })
        else:
            warnings.append({
                "type": "no_template_validation",
                "message": "Template loader not available, skipping artifact type validation"
            })

        # Check 5: Events file parseable (implicit - if we got here, it parsed)
        # No explicit check needed

        # Check 6: Version alignment (pyproject.toml vs git tag)
        issues.extend(self._check_version_alignment(repo_root))

        # Summary
        is_healthy = len(issues) == 0
        return {
            "healthy": is_healthy,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "total_artifacts": len(list(self.tg.graph.nodes())),
                "total_links": len(list(self.tg.graph.edges())),
                "issue_count": len(issues),
                "warning_count": len(warnings),
            }
        }

    def sync_with_git(self, repo_root: Path | None = None) -> dict:
        """Detect changes between trace state and git repository.

        Detects:
        - Added files (in git but not traced)
        - Deleted files (traced but not in git)
        - Renamed files (using git rename detection)

        Args:
            repo_root: Path to git repo root (defaults to cwd)

        Returns:
            Dict with detected changes
        """
        if repo_root is None:
            repo_root = Path.cwd()

        # Get git-tracked files
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            git_files = set(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError as e:
            return {
                "error": f"Failed to get git files: {e}",
                "added_files": [],
                "deleted_files": [],
                "renamed_files": [],
            }

        # Get all traced file paths
        traced_files = {}  # file_path -> artifact_id
        for artifact_id in self.tg.graph.nodes():
            artifact = self.tg.get_artifact(artifact_id)
            if artifact and artifact.get("file_path"):
                traced_files[artifact["file_path"]] = artifact_id

        # Detect added files (in git but not traced)
        added_files = []
        for git_file in git_files:
            if git_file and git_file not in traced_files:
                # Suggest artifact type based on templates
                suggested_type = None
                if self.template_loader:
                    suggested_type = self.template_loader.classify_file(git_file)

                added_files.append({
                    "file_path": git_file,
                    "suggested_type": suggested_type or "document",
                })

        # Detect deleted files (traced but not in git)
        deleted_files = []
        for file_path, artifact_id in traced_files.items():
            if file_path not in git_files:
                deleted_files.append({
                    "file_path": file_path,
                    "artifact_id": artifact_id,
                })

        # Detect renamed files using git diff with rename detection
        renamed_files = []
        try:
            # Get renames between last commit and working tree
            result = subprocess.run(
                ["git", "diff", "--name-status", "--diff-filter=R", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output: "R<score>\told_path\tnew_path"
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    old_path = parts[1]
                    new_path = parts[2]

                    # Check if old_path is traced
                    if old_path in traced_files:
                        artifact_id = traced_files[old_path]
                        renamed_files.append({
                            "artifact_id": artifact_id,
                            "old_path": old_path,
                            "new_path": new_path,
                        })
        except subprocess.CalledProcessError:
            # No renames or error - not critical
            pass

        return {
            "added_files": added_files,
            "deleted_files": deleted_files,
            "renamed_files": renamed_files,
            "summary": {
                "added_count": len(added_files),
                "deleted_count": len(deleted_files),
                "renamed_count": len(renamed_files),
            }
        }

    def accept_all_proposed(self) -> dict:
        """Promote all proposed links to authoritative state.

        Returns:
            Dict with count of promoted links
        """
        from .events import EventLog
        from .models import Event, EventType

        promoted = []
        proposed = self.proposed_links()

        for u, v, d in proposed:
            # Create promotion event
            payload = {
                "source_id": u,
                "target_id": v,
            }
            event = Event(
                event_type=EventType.LINK_PROMOTED,
                payload=payload,
                actor="human",
                state=State.AUTHORITATIVE,
            )

            # Apply to graph first
            self.tg._apply_event(event)

            # Append to event log
            self.tg.event_log.append(event)

            promoted.append({"source": u, "target": v, "relationship_type": d.get("relationship_type")})

        return {
            "promoted_links": promoted,
            "count": len(promoted),
        }

    def accept_by_type(self, relationship_type: str) -> dict:
        """Promote proposed links of a specific relationship type to authoritative.

        Args:
            relationship_type: The relationship type to promote

        Returns:
            Dict with count of promoted links
        """
        from .events import EventLog
        from .models import Event, EventType

        promoted = []
        proposed = self.proposed_links()

        for u, v, d in proposed:
            if d.get("relationship_type") == relationship_type:
                # Create promotion event
                payload = {
                    "source_id": u,
                    "target_id": v,
                }
                event = Event(
                    event_type=EventType.LINK_PROMOTED,
                    payload=payload,
                    actor="human",
                    state=State.AUTHORITATIVE,
                )

                # Apply to graph first
                self.tg._apply_event(event)

                # Append to event log
                self.tg.event_log.append(event)

                promoted.append({"source": u, "target": v, "relationship_type": d.get("relationship_type")})

        return {
            "relationship_type": relationship_type,
            "promoted_links": promoted,
            "count": len(promoted),
        }

    def accept_by_source(self, artifact_id: str) -> dict:
        """Promote all proposed links from a specific source artifact to authoritative.

        Args:
            artifact_id: The source artifact ID

        Returns:
            Dict with count of promoted links
        """
        from .events import EventLog
        from .models import Event, EventType

        if artifact_id not in self.tg.graph:
            return {"error": f"Artifact not found: {artifact_id}"}

        promoted = []
        proposed = self.proposed_links()

        for u, v, d in proposed:
            if u == artifact_id:
                # Create promotion event
                payload = {
                    "source_id": u,
                    "target_id": v,
                }
                event = Event(
                    event_type=EventType.LINK_PROMOTED,
                    payload=payload,
                    actor="human",
                    state=State.AUTHORITATIVE,
                )

                # Apply to graph first
                self.tg._apply_event(event)

                # Append to event log
                self.tg.event_log.append(event)

                promoted.append({"source": u, "target": v, "relationship_type": d.get("relationship_type")})

        return {
            "source_artifact": artifact_id,
            "promoted_links": promoted,
            "count": len(promoted),
        }

    def register_file(self, file_path: str) -> dict:
        """Auto-classify and register a file as an artifact.

        Implements REQ-AUTO-001: Zero-friction file registration.

        Args:
            file_path: Relative path to file

        Returns:
            Dict with artifact_id, artifact_type, success, already_exists
        """
        from .models import Event, EventType

        # Check if already registered
        if file_path in self.tg.graph:
            artifact = self.tg.get_artifact(file_path)
            return {
                "artifact_id": file_path,
                "artifact_type": artifact.get("artifact_type") if artifact else "unknown",
                "already_exists": True,
                "success": True
            }

        # Auto-classify using template loader
        artifact_type = "document"  # default
        if self.template_loader:
            classified = self.template_loader.classify_file(file_path)
            if classified:
                artifact_type = classified

        # Register
        payload = {
            "artifact_id": file_path,
            "artifact_type": artifact_type,
            "file_path": file_path,
        }

        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload=payload,
            actor="ai:auto-capture",
            state=State.PROPOSED,
        )

        # Apply to graph first
        self.tg._apply_event(event)

        # Append to event log
        self.tg.event_log.append(event)

        return {
            "artifact_id": file_path,
            "artifact_type": artifact_type,
            "already_exists": False,
            "success": True
        }

    def check_impact(self, artifact_id: str, threshold: int = 3) -> dict:
        """Check impact and return warning if above threshold.

        Implements REQ-IMPACT-001: Proactive impact warnings.

        Args:
            artifact_id: Artifact to check
            threshold: Warn if downstream count exceeds this (default: 3)

        Returns:
            Dict with downstream list, count, exceeds_threshold, warning message
        """
        downstream = self.impact(artifact_id)
        count = len(downstream)
        exceeds = count > threshold

        warning = None
        if exceeds:
            preview = downstream[:5]
            warning = f"⚠️ {artifact_id} has {count} downstream dependencies. Modifications may affect: {', '.join(preview)}"
            if count > 5:
                warning += f" and {count - 5} more."

        return {
            "artifact_id": artifact_id,
            "downstream": downstream,
            "count": count,
            "threshold": threshold,
            "exceeds_threshold": exceeds,
            "warning": warning
        }

    def infer_dependencies(
        self,
        file_path: str,
        repo_root: Path = None,
        auto_propose: bool = False
    ) -> dict:
        """Infer depends_on relationships from file imports/references.

        Implements REQ-INFER-001: Automatic relationship inference.

        For Python files: parses imports, maps to traced artifacts
        For Markdown files: parses links, maps to traced artifacts

        Args:
            file_path: Relative path to file to analyze
            repo_root: Repository root for file access (defaults to cwd)
            auto_propose: If True, automatically propose links. If False, dry-run.

        Returns:
            Dict with dependencies list, proposed_count, skipped_count
        """
        from .models import Event, EventType
        from .parsers.python_ast import PythonParser
        from .parsers.markdown import MarkdownParser

        if repo_root is None:
            repo_root = Path.cwd()

        full_path = repo_root / file_path
        if not full_path.exists():
            return {
                "file_path": file_path,
                "dependencies": [],
                "proposed_count": 0,
                "skipped_count": 0,
                "error": f"File not found: {file_path}"
            }

        dependencies = []
        skipped = 0

        # Determine file type and parse accordingly
        if file_path.endswith('.py'):
            # Parse Python imports
            parser = PythonParser()
            imports = parser.parse_imports(full_path)

            for import_path in imports:
                # Try to map import to a file path
                artifact_id = self._map_python_import_to_artifact(import_path, repo_root)

                if artifact_id and artifact_id in self.tg.graph:
                    dependencies.append({
                        "source": file_path,
                        "target": artifact_id,
                        "relationship_type": "depends_on",
                        "rationale": f"Imports {import_path} from {artifact_id}"
                    })
                else:
                    skipped += 1

        elif file_path.endswith('.md'):
            # Parse Markdown links
            parser = MarkdownParser()
            links = parser.parse_links(full_path)

            for link in links:
                # Resolve relative link
                link_path = (full_path.parent / link).resolve()
                try:
                    artifact_id = str(link_path.relative_to(repo_root))
                except ValueError:
                    # Link is outside repo
                    skipped += 1
                    continue

                if artifact_id in self.tg.graph:
                    dependencies.append({
                        "source": file_path,
                        "target": artifact_id,
                        "relationship_type": "references",
                        "rationale": f"Links to {artifact_id}"
                    })
                else:
                    skipped += 1

        # Auto-propose if requested
        proposed_count = 0
        if auto_propose and dependencies:
            for dep in dependencies:
                # Check if link already exists
                if self.tg.graph.has_edge(dep["source"], dep["target"]):
                    continue

                payload = {
                    "source_id": dep["source"],
                    "target_id": dep["target"],
                    "relationship_type": dep["relationship_type"],
                }

                event = Event(
                    event_type=EventType.LINK_ADDED,
                    payload=payload,
                    actor="ai:infer-dependencies",
                    state=State.PROPOSED,
                    rationale=dep["rationale"],
                )

                self.tg._apply_event(event)
                self.tg.event_log.append(event)
                proposed_count += 1

        return {
            "file_path": file_path,
            "dependencies": dependencies,
            "proposed_count": proposed_count,
            "skipped_count": skipped,
        }

    def _map_python_import_to_artifact(self, import_path: str, repo_root: Path) -> str | None:
        """Map Python import path to artifact ID (file path).

        Examples:
            trace_core.models → src/trace_core/models.py
            mcp_server.server → mcp_server/server.py
        """
        parts = import_path.split('.')

        # Try common patterns
        candidates = []

        if parts[0] == 'trace_core':
            # src/trace_core/...
            candidates.append(repo_root / 'src' / '/'.join(parts))
        elif parts[0] == 'mcp_server':
            # mcp_server/...
            candidates.append(repo_root / '/'.join(parts))
        else:
            # Try direct path
            candidates.append(repo_root / '/'.join(parts))

        # Try each candidate
        for candidate in candidates:
            py_file = candidate.with_suffix('.py')
            if py_file.exists():
                try:
                    return str(py_file.relative_to(repo_root))
                except ValueError:
                    pass

            # Try __init__.py
            init_file = candidate / '__init__.py'
            if init_file.exists():
                try:
                    return str(init_file.relative_to(repo_root))
                except ValueError:
                    pass

        return None
