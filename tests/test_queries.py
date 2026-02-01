"""Tests for query functionality."""
import tempfile
from pathlib import Path

import pytest

from trace_core import Event, EventLog, TraceGraph, TraceQueries
from trace_core.models import EventType, State


@pytest.fixture
def populated_queries():
    """Create queries instance with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = EventLog(Path(tmpdir) / ".trace")
        log.init()

        # Create a chain: REQ-001 <- MOD-001 <- TEST-001
        for aid, atype in [("REQ-001", "requirement"), ("MOD-001", "module"), ("TEST-001", "test")]:
            log.append(Event(
                event_type=EventType.ARTIFACT_ADDED,
                payload={"artifact_id": aid, "artifact_type": atype},
            ))

        log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={"source_id": "MOD-001", "target_id": "REQ-001", "relationship_type": "implements"},
            state=State.AUTHORITATIVE,
        ))
        log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={"source_id": "TEST-001", "target_id": "MOD-001", "relationship_type": "verifies"},
            state=State.PROPOSED,
        ))

        graph = TraceGraph(log)
        graph.rebuild()
        queries = TraceQueries(graph)

        yield queries


def test_trace_query(populated_queries):
    """Test trace returns upstream and downstream."""
    result = populated_queries.trace("MOD-001")
    assert "REQ-001" in result["downstream"]
    assert "TEST-001" in result["upstream"]


def test_impact_query(populated_queries):
    """Test impact returns transitive downstream."""
    result = populated_queries.impact("TEST-001")
    assert "MOD-001" in result
    assert "REQ-001" in result


def test_orphans_query():
    """Test orphans finds unlinked artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = EventLog(Path(tmpdir) / ".trace")
        log.init()

        log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "ORPHAN-001", "artifact_type": "requirement"},
        ))

        graph = TraceGraph(log)
        graph.rebuild()
        queries = TraceQueries(graph)

        assert "ORPHAN-001" in queries.orphans()


def test_proposed_links(populated_queries):
    """Test finding proposed links."""
    proposed = populated_queries.proposed_links()
    assert len(proposed) == 1
    assert proposed[0][0] == "TEST-001"
    assert proposed[0][1] == "MOD-001"
