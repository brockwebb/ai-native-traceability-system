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

    def health_check(self, repo_root: Path | None = None) -> dict:
        """Validate trace data integrity.

        Checks:
        - All artifact file_paths exist in git
        - No broken links (source or target artifact missing)
        - No duplicate artifact IDs
        - All artifact_types are valid per loaded templates
        - Events file is parseable (implicit if we loaded successfully)

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
