"""Shared test fixtures for the traceability system."""
import tempfile
from pathlib import Path

import pytest

from trace_core import Event, EventLog, TraceGraph, ReportGenerator
from trace_core.models import EventType, State


@pytest.fixture
def temp_trace_dir():
    """Create temporary trace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / ".trace"


@pytest.fixture
def event_log(temp_trace_dir):
    """Create initialized event log."""
    log = EventLog(temp_trace_dir)
    log.init()
    return log


@pytest.fixture
def empty_graph(event_log):
    """Create empty trace graph."""
    graph = TraceGraph(event_log)
    graph.rebuild()
    return graph


@pytest.fixture
def graph_with_data(event_log):
    """Create graph with sample artifacts and links."""
    # Add requirements
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "REQ-001", "artifact_type": "requirement"},
    ))
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "REQ-002", "artifact_type": "requirement"},
    ))

    # Add modules
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "auth.py", "artifact_type": "module", "file_path": "src/auth.py"},
    ))
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "api.py", "artifact_type": "module", "file_path": "src/api.py"},
    ))

    # Add tests
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "test_auth.py", "artifact_type": "test", "file_path": "tests/test_auth.py"},
    ))

    # Add links - auth.py implements REQ-001
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "auth.py",
            "target_id": "REQ-001",
            "relationship_type": "implements",
        },
        state=State.AUTHORITATIVE,
    ))

    # test_auth.py verifies auth.py
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "test_auth.py",
            "target_id": "auth.py",
            "relationship_type": "verifies",
        },
        state=State.AUTHORITATIVE,
    ))

    # api.py depends on auth.py
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "api.py",
            "target_id": "auth.py",
            "relationship_type": "depends_on",
        },
        state=State.AUTHORITATIVE,
    ))

    graph = TraceGraph(event_log)
    graph.rebuild()
    return graph


@pytest.fixture
def graph_with_orphans(event_log):
    """Create graph with orphan requirements and untested modules."""
    # Orphan requirement (nothing implements it)
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "REQ-ORPHAN", "artifact_type": "requirement"},
    ))

    # Untested module (nothing verifies it)
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "untested.py", "artifact_type": "module"},
    ))

    # Complete requirement with implementation and test
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "REQ-COMPLETE", "artifact_type": "requirement"},
    ))
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "complete.py", "artifact_type": "module"},
    ))
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "test_complete.py", "artifact_type": "test"},
    ))

    # Links
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "complete.py",
            "target_id": "REQ-COMPLETE",
            "relationship_type": "implements",
        },
        state=State.AUTHORITATIVE,
    ))
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "test_complete.py",
            "target_id": "complete.py",
            "relationship_type": "verifies",
        },
        state=State.AUTHORITATIVE,
    ))

    graph = TraceGraph(event_log)
    graph.rebuild()
    return graph


@pytest.fixture
def graph_with_decisions(event_log):
    """Create graph with decision records."""
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "DEC-001-database-choice",
            "artifact_type": "decision",
            "file_path": "docs/decisions/001-database.md",
            "tags": ["architecture"],
        },
    ))
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "DEC-002-api-framework",
            "artifact_type": "decision",
            "file_path": "docs/decisions/002-api-framework.md",
            "tags": ["architecture", "api"],
        },
    ))

    # Undocumented decision (not linked to anything)
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "DEC-003-orphan",
            "artifact_type": "decision",
        },
    ))

    # Link decision to artifact
    event_log.append(Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={"artifact_id": "database.py", "artifact_type": "module"},
    ))
    event_log.append(Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "database.py",
            "target_id": "DEC-001-database-choice",
            "relationship_type": "implements",
        },
        state=State.AUTHORITATIVE,
    ))

    graph = TraceGraph(event_log)
    graph.rebuild()
    return graph


@pytest.fixture
def large_graph(event_log):
    """Create larger graph for impact analysis."""
    # Create a dependency chain: A -> B -> C -> D
    for i, name in enumerate(["A", "B", "C", "D"]):
        event_log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": name, "artifact_type": "module"},
        ))

    # Create links
    for source, target in [("A", "B"), ("B", "C"), ("C", "D")]:
        event_log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": source,
                "target_id": target,
                "relationship_type": "depends_on",
            },
            state=State.AUTHORITATIVE,
        ))

    graph = TraceGraph(event_log)
    graph.rebuild()
    return graph


@pytest.fixture
def report_generator(graph_with_data):
    """Create report generator with sample data."""
    return ReportGenerator(graph_with_data)
