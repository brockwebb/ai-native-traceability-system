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


def test_version_mismatch_detected(tmp_path, monkeypatch):
    """Health check detects version/tag mismatch."""
    # Setup: pyproject.toml with version 0.3.0
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "0.3.0"')

    # Mock git to return v0.4.0 tag
    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = "v0.4.0\n"
        return Result()

    monkeypatch.setattr("subprocess.run", mock_run)

    # Setup minimal trace
    log = EventLog(tmp_path / ".trace")
    log.init()
    graph = TraceGraph(log)
    graph.rebuild()
    queries = TraceQueries(graph)

    # Run health check
    result = queries.health_check(tmp_path)

    # Should have version_mismatch issue
    version_issues = [i for i in result["issues"] if i["type"] == "version_mismatch"]
    assert len(version_issues) == 1
    assert "0.3.0" in version_issues[0]["message"]
    assert "v0.4.0" in version_issues[0]["message"]


def test_version_match_no_issue(tmp_path, monkeypatch):
    """Health check passes when versions align."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nversion = "0.4.0"')

    def mock_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = "v0.4.0\n"
        return Result()

    monkeypatch.setattr("subprocess.run", mock_run)

    # Setup minimal trace
    log = EventLog(tmp_path / ".trace")
    log.init()
    graph = TraceGraph(log)
    graph.rebuild()
    queries = TraceQueries(graph)

    result = queries.health_check(tmp_path)

    version_issues = [i for i in result["issues"] if i["type"] == "version_mismatch"]
    assert len(version_issues) == 0


def test_no_pyproject_skips_check(tmp_path):
    """Health check skips version check if no pyproject.toml."""
    # Setup minimal trace
    log = EventLog(tmp_path / ".trace")
    log.init()
    graph = TraceGraph(log)
    graph.rebuild()
    queries = TraceQueries(graph)

    result = queries.health_check(tmp_path)

    version_issues = [i for i in result["issues"] if i["type"] == "version_mismatch"]
    assert len(version_issues) == 0
