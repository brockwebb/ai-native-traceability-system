"""Tests for graph projection functionality."""
import tempfile
from pathlib import Path

import pytest

from trace_core import Event, EventLog, TraceGraph
from trace_core.models import EventType, State


def test_graph_rebuild_from_events():
    """Test graph rebuilds correctly from event log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = EventLog(Path(tmpdir) / ".trace")
        log.init()

        # Add artifacts
        log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "REQ-001", "artifact_type": "requirement"},
        ))
        log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "MOD-001", "artifact_type": "module"},
        ))

        # Add link
        log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": "MOD-001",
                "target_id": "REQ-001",
                "relationship_type": "implements",
            },
            state=State.PROPOSED,
        ))

        graph = TraceGraph(log)
        graph.rebuild()

        assert "REQ-001" in graph.graph
        assert "MOD-001" in graph.graph
        assert graph.graph.has_edge("MOD-001", "REQ-001")


def test_graph_neighbors():
    """Test getting neighbors from graph."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = EventLog(Path(tmpdir) / ".trace")
        log.init()

        log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "A", "artifact_type": "requirement"},
        ))
        log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "B", "artifact_type": "module"},
        ))
        log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={"source_id": "B", "target_id": "A", "relationship_type": "implements"},
        ))

        graph = TraceGraph(log)
        graph.rebuild()

        assert graph.get_neighbors("A", "upstream") == ["B"]
        assert graph.get_neighbors("B", "downstream") == ["A"]
