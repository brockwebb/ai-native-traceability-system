"""Tests for MCP server auto-reload functionality."""
import tempfile
import time
from pathlib import Path

from mcp_server.server import TraceabilityServer
from trace_core import Event, EventLog, EventType, State


def test_server_auto_reload_on_file_change():
    """Test that server automatically reloads when events.jsonl changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / ".trace"
        trace_dir.mkdir()

        # Initialize server
        server = TraceabilityServer(str(trace_dir))

        # Initially should have no artifacts
        result = server._handle_list_artifacts({})
        assert result["count"] == 0

        # Wait a bit to ensure different mtime
        time.sleep(0.1)

        # Add an artifact directly via EventLog (simulating external script)
        event_log = EventLog(str(trace_dir))
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": "test-artifact",
                "artifact_type": "module",
                "file_path": "test.py",
            },
            actor="external-script",
            state=State.PROPOSED,
        )
        event_log.append(event)

        # Query server again - should auto-reload and see new artifact
        result = server._handle_list_artifacts({})
        assert result["count"] == 1
        assert result["artifacts"][0]["artifact_id"] == "test-artifact"


def test_server_no_reload_if_file_unchanged():
    """Test that server doesn't reload unnecessarily."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / ".trace"
        trace_dir.mkdir()

        # Initialize server
        server = TraceabilityServer(str(trace_dir))

        # Query once
        result1 = server._handle_list_artifacts({})

        # Store graph object ID
        graph_id_1 = id(server._graph)

        # Query again immediately (no file change)
        result2 = server._handle_list_artifacts({})

        # Should be same graph object (no reload)
        graph_id_2 = id(server._graph)
        assert graph_id_1 == graph_id_2


def test_server_reload_updates_all_components():
    """Test that reload updates graph, queries, and template_loader."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / ".trace"
        trace_dir.mkdir()
        (trace_dir / "templates").mkdir()

        # Initialize server
        server = TraceabilityServer(str(trace_dir))

        # Store initial object IDs
        graph_id_1 = id(server._graph)
        queries_id_1 = id(server._queries)

        # Wait and add artifact
        time.sleep(0.1)
        event_log = EventLog(str(trace_dir))
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": "test-module",
                "artifact_type": "module",
            },
            actor="test",
            state=State.PROPOSED,
        )
        event_log.append(event)

        # Access properties to trigger reload
        _ = server.graph
        _ = server.queries

        # Should have new objects
        graph_id_2 = id(server._graph)
        queries_id_2 = id(server._queries)

        assert graph_id_1 != graph_id_2
        assert queries_id_1 != queries_id_2
