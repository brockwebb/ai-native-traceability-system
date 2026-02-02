"""Tests for REQ-HC-001: Health Check MCP Tool."""
import json
import subprocess
from pathlib import Path
import pytest

from trace_core import EventLog, Event, EventType, State, TraceGraph, TraceQueries, TemplateLoader


@pytest.fixture
def trace_setup(tmp_path):
    """Set up a temporary trace environment with git."""
    trace_dir = tmp_path / ".trace"
    trace_dir.mkdir()
    (trace_dir / "templates").mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)

    # Create a test file and add to git
    test_file = tmp_path / "test.py"
    test_file.write_text("# test file\n")
    subprocess.run(["git", "add", "test.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)

    # Create event log and graph
    event_log = EventLog(str(trace_dir))
    event_log.init()
    graph = TraceGraph(event_log)

    # Create template loader with a simple template
    template_path = trace_dir / "templates" / "test-template.yaml"
    template_path.write_text("""
name: Test Template
artifact_types:
  - id: module
    name: Code Module
  - id: test
    name: Test
""")

    template_loader = TemplateLoader(trace_dir / "templates")
    queries = TraceQueries(graph, template_loader)

    return {
        "tmp_path": tmp_path,
        "trace_dir": trace_dir,
        "event_log": event_log,
        "graph": graph,
        "queries": queries,
        "template_loader": template_loader,
    }


def test_req_hc_001_healthy_trace(trace_setup):
    """REQ-HC-001: Health check passes on valid trace data."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifact with valid file path
    event = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "test.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event)
    graph._apply_event(event)

    # Run health check
    result = queries.health_check(trace_setup["tmp_path"])

    assert result["healthy"] is True
    assert result["summary"]["issue_count"] == 0
    assert result["summary"]["total_artifacts"] == 1


def test_req_hc_001_missing_file(trace_setup):
    """REQ-HC-001: Health check detects missing files."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifact with non-existent file path
    event = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "nonexistent.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event)
    graph._apply_event(event)

    # Run health check
    result = queries.health_check(trace_setup["tmp_path"])

    assert result["healthy"] is False
    assert result["summary"]["issue_count"] == 1
    assert result["issues"][0]["type"] == "missing_file"
    assert result["issues"][0]["artifact_id"] == "test-001"
    assert "nonexistent.py" in result["issues"][0]["message"]


def test_req_hc_001_broken_link(trace_setup):
    """REQ-HC-001: Health check detects broken links."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifact
    event1 = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "test.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event1)
    graph._apply_event(event1)

    # Add link to non-existent target
    event2 = Event(
        event_type=EventType.LINK_ADDED,
        payload={
            "source_id": "test-001",
            "target_id": "nonexistent-002",
            "relationship_type": "depends_on"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event2)
    # Note: _apply_event will add edge even if target doesn't exist as a node
    # This is the broken state we want to detect
    graph.graph.add_edge("test-001", "nonexistent-002",
                        relationship_type="depends_on",
                        state=State.AUTHORITATIVE.value)

    # Run health check
    result = queries.health_check(trace_setup["tmp_path"])

    assert result["healthy"] is False
    assert result["summary"]["issue_count"] >= 1
    broken_links = [i for i in result["issues"] if i["type"] == "broken_link"]
    assert len(broken_links) >= 1
    assert broken_links[0]["target_id"] == "nonexistent-002"


def test_req_hc_001_invalid_artifact_type(trace_setup):
    """REQ-HC-001: Health check detects invalid artifact types."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifact with invalid type
    event = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "invalid_type",
            "file_path": "test.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event)
    graph._apply_event(event)

    # Run health check
    result = queries.health_check(trace_setup["tmp_path"])

    # Should have warning (not issue) for unknown type
    assert result["summary"]["warning_count"] >= 1
    type_warnings = [w for w in result["warnings"] if w["type"] == "unknown_artifact_type"]
    assert len(type_warnings) == 1
    assert type_warnings[0]["artifact_type"] == "invalid_type"


def test_req_hc_001_multiple_issues(trace_setup):
    """REQ-HC-001: Health check detects multiple issues."""
    event_log = trace_setup["event_log"]
    graph = trace_setup["graph"]
    queries = trace_setup["queries"]

    # Add artifact with missing file
    event1 = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "missing1.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event1)
    graph._apply_event(event1)

    # Add another artifact with missing file
    event2 = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-002",
            "artifact_type": "module",
            "file_path": "missing2.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event2)
    graph._apply_event(event2)

    # Run health check
    result = queries.health_check(trace_setup["tmp_path"])

    assert result["healthy"] is False
    assert result["summary"]["issue_count"] == 2
    assert result["summary"]["total_artifacts"] == 2


def test_req_hc_001_structured_report(trace_setup):
    """REQ-HC-001: Health check returns structured report."""
    queries = trace_setup["queries"]

    # Run health check on empty graph
    result = queries.health_check(trace_setup["tmp_path"])

    # Verify report structure
    assert "healthy" in result
    assert "issues" in result
    assert "warnings" in result
    assert "summary" in result

    # Verify summary structure
    assert "total_artifacts" in result["summary"]
    assert "total_links" in result["summary"]
    assert "issue_count" in result["summary"]
    assert "warning_count" in result["summary"]

    assert isinstance(result["healthy"], bool)
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)
