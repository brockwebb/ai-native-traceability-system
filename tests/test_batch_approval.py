"""Tests for REQ-BA-001: Batch Approval Tools."""
from pathlib import Path
import pytest

from trace_core import EventLog, Event, EventType, State, TraceGraph, TraceQueries


@pytest.fixture
def trace_setup(tmp_path):
    """Set up a temporary trace environment."""
    trace_dir = tmp_path / ".trace"
    trace_dir.mkdir()

    # Create event log and graph
    event_log = EventLog(str(trace_dir))
    event_log.init()
    graph = TraceGraph(event_log)
    queries = TraceQueries(graph)

    return {
        "tmp_path": tmp_path,
        "trace_dir": trace_dir,
        "event_log": event_log,
        "graph": graph,
        "queries": queries,
    }


def test_req_ba_001_accept_all_proposed(trace_setup):
    """REQ-BA-001: Accept all proposed links at once."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add two artifacts
    for i in range(1, 3):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Add two proposed links
    for i in range(1, 3):
        event = Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": "test-001",
                "target_id": f"test-{i+1:03d}" if i == 1 else "test-001",
                "relationship_type": "depends_on"
            },
            actor="ai",
            state=State.PROPOSED,
            rationale="test link"
        )
        event_log.append(event)
        graph._apply_event(event)

    # Verify we have 2 proposed links
    proposed = queries.proposed_links()
    assert len(proposed) == 2

    # Accept all proposed
    result = queries.accept_all_proposed()

    assert result["count"] == 2
    assert len(result["promoted_links"]) == 2

    # Verify all links are now authoritative
    proposed_after = queries.proposed_links()
    assert len(proposed_after) == 0


def test_req_ba_001_accept_by_type(trace_setup):
    """REQ-BA-001: Accept proposed links filtered by relationship type."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifacts
    for i in range(1, 4):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Add proposed links with different types
    links = [
        ("test-001", "test-002", "implements"),
        ("test-001", "test-003", "depends_on"),
        ("test-002", "test-003", "implements"),
    ]

    for source, target, rel_type in links:
        event = Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": source,
                "target_id": target,
                "relationship_type": rel_type
            },
            actor="ai",
            state=State.PROPOSED,
            rationale="test link"
        )
        event_log.append(event)
        graph._apply_event(event)

    # Verify we have 3 proposed links
    proposed = queries.proposed_links()
    assert len(proposed) == 3

    # Accept only "implements" links
    result = queries.accept_by_type("implements")

    assert result["count"] == 2
    assert result["relationship_type"] == "implements"
    assert len(result["promoted_links"]) == 2

    # Verify we still have 1 proposed link (depends_on)
    proposed_after = queries.proposed_links()
    assert len(proposed_after) == 1
    assert proposed_after[0][2]["relationship_type"] == "depends_on"


def test_req_ba_001_accept_by_source(trace_setup):
    """REQ-BA-001: Accept all proposed links from a specific source artifact."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifacts
    for i in range(1, 5):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Add proposed links from different sources
    links = [
        ("test-001", "test-002", "depends_on"),
        ("test-001", "test-003", "implements"),
        ("test-002", "test-004", "depends_on"),
    ]

    for source, target, rel_type in links:
        event = Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": source,
                "target_id": target,
                "relationship_type": rel_type
            },
            actor="ai",
            state=State.PROPOSED,
            rationale="test link"
        )
        event_log.append(event)
        graph._apply_event(event)

    # Verify we have 3 proposed links
    proposed = queries.proposed_links()
    assert len(proposed) == 3

    # Accept only links from test-001
    result = queries.accept_by_source("test-001")

    assert result["count"] == 2
    assert result["source_artifact"] == "test-001"
    assert len(result["promoted_links"]) == 2

    # Verify we still have 1 proposed link (from test-002)
    proposed_after = queries.proposed_links()
    assert len(proposed_after) == 1
    assert proposed_after[0][0] == "test-002"


def test_req_ba_001_accept_all_when_empty(trace_setup):
    """REQ-BA-001: Accept all when no proposed links exist."""
    queries = trace_setup["queries"]

    # No proposed links
    result = queries.accept_all_proposed()

    assert result["count"] == 0
    assert len(result["promoted_links"]) == 0


def test_req_ba_001_accept_by_type_no_matches(trace_setup):
    """REQ-BA-001: Accept by type when no links of that type exist."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifacts
    for i in range(1, 3):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Add proposed link with "depends_on" type
    event = Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "test-001",
            "target_id": "test-002",
            "relationship_type": "depends_on"
        },
        actor="ai",
        state=State.PROPOSED,
        rationale="test link"
    )
    event_log.append(event)
    graph._apply_event(event)

    # Try to accept "implements" links (none exist)
    result = queries.accept_by_type("implements")

    assert result["count"] == 0
    assert len(result["promoted_links"]) == 0

    # Original link should still be proposed
    proposed = queries.proposed_links()
    assert len(proposed) == 1


def test_req_ba_001_accept_by_source_invalid_artifact(trace_setup):
    """REQ-BA-001: Accept by source with invalid artifact ID."""
    queries = trace_setup["queries"]

    result = queries.accept_by_source("nonexistent-001")

    assert "error" in result
    assert "not found" in result["error"].lower()


def test_req_ba_001_events_persisted(trace_setup):
    """REQ-BA-001: Batch approval events are persisted to event log."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifacts
    for i in range(1, 3):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Add proposed link
    event = Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "test-001",
            "target_id": "test-002",
            "relationship_type": "depends_on"
        },
        actor="ai",
        state=State.PROPOSED,
        rationale="test link"
    )
    event_log.append(event)
    graph._apply_event(event)

    # Count events before promotion
    events_before = list(event_log.iter_events())
    count_before = len(events_before)

    # Accept all proposed
    result = queries.accept_all_proposed()

    # Count events after promotion
    events_after = list(event_log.iter_events())
    count_after = len(events_after)

    # Should have 1 additional LINK_PROMOTED event
    assert count_after == count_before + 1

    # Verify the new event is LINK_PROMOTED
    last_event = events_after[-1]
    assert last_event.event_type == EventType.LINK_PROMOTED
    assert last_event.payload["source_id"] == "test-001"
    assert last_event.payload["target_id"] == "test-002"
    assert last_event.actor == "human"
