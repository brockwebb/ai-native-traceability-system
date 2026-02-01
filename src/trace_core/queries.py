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
