"""NetworkX graph projection from event log."""
import networkx as nx

from .models import Event, EventType, State
from .events import EventLog


class TraceGraph:
    """In-memory graph projection of the trace event log."""

    def __init__(self, event_log: EventLog):
        self.event_log = event_log
        self.graph: nx.DiGraph = nx.DiGraph()
        self._artifacts: dict[str, dict] = {}  # artifact_id -> metadata

    def rebuild(self) -> None:
        """Rebuild graph from event log (call on load)."""
        self.graph.clear()
        self._artifacts.clear()

        for event in self.event_log.iter_events():
            self._apply_event(event)

    def _apply_event(self, event: Event) -> None:
        """Apply a single event to the graph."""
        payload = event.payload

        if event.event_type == EventType.ARTIFACT_ADDED:
            artifact_id = payload["artifact_id"]
            self.graph.add_node(artifact_id, **payload, state=event.state.value)
            self._artifacts[artifact_id] = payload

        elif event.event_type == EventType.ARTIFACT_REMOVED:
            artifact_id = payload["artifact_id"]
            if artifact_id in self.graph:
                self.graph.remove_node(artifact_id)
            self._artifacts.pop(artifact_id, None)

        elif event.event_type == EventType.LINK_ADDED:
            source = payload["source_id"]
            target = payload["target_id"]
            rel_type = payload["relationship_type"]
            self.graph.add_edge(
                source, target,
                relationship_type=rel_type,
                state=event.state.value,
                rationale=event.rationale,
            )

        elif event.event_type == EventType.LINK_REMOVED:
            source = payload["source_id"]
            target = payload["target_id"]
            if self.graph.has_edge(source, target):
                self.graph.remove_edge(source, target)

        elif event.event_type == EventType.LINK_PROMOTED:
            source = payload["source_id"]
            target = payload["target_id"]
            if self.graph.has_edge(source, target):
                self.graph.edges[source, target]["state"] = State.AUTHORITATIVE.value

    def get_artifact(self, artifact_id: str) -> dict | None:
        """Get artifact metadata by ID."""
        return self._artifacts.get(artifact_id)

    def get_neighbors(self, artifact_id: str, direction: str = "both") -> list[str]:
        """Get neighboring artifacts."""
        if artifact_id not in self.graph:
            return []
        if direction == "upstream":
            return list(self.graph.predecessors(artifact_id))
        elif direction == "downstream":
            return list(self.graph.successors(artifact_id))
        else:
            preds = set(self.graph.predecessors(artifact_id))
            succs = set(self.graph.successors(artifact_id))
            return list(preds | succs)
