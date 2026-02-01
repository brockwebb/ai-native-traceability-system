"""Query functions for the trace graph."""
from typing import Any

import networkx as nx

from .graph import TraceGraph
from .models import State


class TraceQueries:
    """High-level queries against the trace graph."""

    def __init__(self, trace_graph: TraceGraph):
        self.tg = trace_graph

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
