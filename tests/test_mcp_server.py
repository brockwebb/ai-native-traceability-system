"""Integration tests for the MCP server."""
import json
import tempfile
from pathlib import Path

import pytest

from mcp_server.server import TraceabilityServer


@pytest.fixture
def temp_trace_dir():
    """Create a temporary trace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def server(temp_trace_dir):
    """Create a server instance with a temporary directory."""
    return TraceabilityServer(temp_trace_dir)


def test_server_initialization(server):
    """Test that server initializes correctly."""
    assert server.event_log is not None
    assert server.graph is not None
    assert server.queries is not None
    assert server.server is not None


def test_add_artifact(server):
    """Test adding an artifact."""
    result = server._handle_add_artifact({
        "artifact_id": "REQ-001",
        "artifact_type": "requirement",
        "file_path": "docs/requirements.md",
        "line_start": 10,
    })

    assert result["success"] is True
    assert result["artifact_id"] == "REQ-001"
    assert result["state"] == "proposed"

    # Verify it was added to the graph
    assert "REQ-001" in server.graph.graph


def test_propose_link(server):
    """Test proposing a link between artifacts."""
    # First add two artifacts
    server._handle_add_artifact({
        "artifact_id": "REQ-001",
        "artifact_type": "requirement",
    })
    server._handle_add_artifact({
        "artifact_id": "CODE-001",
        "artifact_type": "function",
    })

    # Propose a link
    result = server._handle_propose_link({
        "source_id": "CODE-001",
        "target_id": "REQ-001",
        "relationship_type": "implements",
        "rationale": "Function implements the requirement",
    })

    assert result["success"] is True
    assert result["source"] == "CODE-001"
    assert result["target"] == "REQ-001"
    assert result["state"] == "proposed"

    # Verify link exists
    assert server.graph.graph.has_edge("CODE-001", "REQ-001")


def test_trace(server):
    """Test tracing an artifact."""
    # Setup: create artifacts and links
    # A (requirement) -> B (implementation) -> C (test)
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "function"})
    server._handle_add_artifact({"artifact_id": "C", "artifact_type": "test"})

    # A -> B (requirement points to implementation)
    server._handle_propose_link({
        "source_id": "A",
        "target_id": "B",
        "relationship_type": "implements",
        "rationale": "B implements A",
    })
    # B -> C (implementation points to test)
    server._handle_propose_link({
        "source_id": "B",
        "target_id": "C",
        "relationship_type": "verifies",
        "rationale": "C verifies B",
    })

    # Trace B: A is upstream (predecessor), C is downstream (successor)
    result = server._handle_trace("B")

    assert result["artifact_id"] == "B"
    assert "A" in result["upstream"]
    assert "C" in result["downstream"]


def test_impact(server):
    """Test impact analysis."""
    # Setup: create a chain A -> B -> C
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "function"})
    server._handle_add_artifact({"artifact_id": "C", "artifact_type": "test"})

    server._handle_propose_link({
        "source_id": "A",
        "target_id": "B",
        "relationship_type": "implements",
        "rationale": "test",
    })
    server._handle_propose_link({
        "source_id": "B",
        "target_id": "C",
        "relationship_type": "verifies",
        "rationale": "test",
    })

    # Check impact of changing A
    result = server._handle_impact("A")

    assert result["artifact_id"] == "A"
    assert "B" in result["affected_artifacts"]
    assert "C" in result["affected_artifacts"]
    assert result["count"] == 2


def test_orphans(server):
    """Test finding orphan artifacts."""
    # Add some connected artifacts
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "function"})
    server._handle_propose_link({
        "source_id": "A",
        "target_id": "B",
        "relationship_type": "implements",
        "rationale": "test",
    })

    # Add an orphan
    server._handle_add_artifact({"artifact_id": "ORPHAN", "artifact_type": "requirement"})

    result = server._handle_orphans()

    assert "ORPHAN" in result["orphan_artifacts"]
    assert "A" not in result["orphan_artifacts"]
    assert "B" not in result["orphan_artifacts"]


def test_proposed_links(server):
    """Test getting proposed links."""
    # Add artifacts and propose a link
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "function"})

    server._handle_propose_link({
        "source_id": "A",
        "target_id": "B",
        "relationship_type": "implements",
        "rationale": "Test link",
    })

    result = server._handle_proposed_links()

    assert result["count"] == 1
    assert len(result["proposed_links"]) == 1
    link = result["proposed_links"][0]
    assert link["source"] == "A"
    assert link["target"] == "B"
    assert link["relationship_type"] == "implements"
    assert link["rationale"] == "Test link"


def test_accept_proposal(server):
    """Test accepting a proposed link."""
    # Setup: create artifacts and propose a link
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "function"})

    server._handle_propose_link({
        "source_id": "A",
        "target_id": "B",
        "relationship_type": "implements",
        "rationale": "Test",
    })

    # Accept the proposal
    result = server._handle_accept_proposal({
        "source_id": "A",
        "target_id": "B",
    })

    assert result["success"] is True
    assert result["state"] == "authoritative"

    # Verify the link is no longer in proposed state
    edge_data = server.graph.graph.edges["A", "B"]
    assert edge_data["state"] == "authoritative"


def test_decisions(server):
    """Test getting decision records."""
    # Add a decision artifact
    server._handle_add_artifact({
        "artifact_id": "DEC-001",
        "artifact_type": "decision",
    })

    # Add a non-decision artifact
    server._handle_add_artifact({
        "artifact_id": "REQ-001",
        "artifact_type": "requirement",
    })

    result = server._handle_decisions()

    assert result["count"] == 1
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["artifact_id"] == "DEC-001"


def test_error_handling_artifact_not_found(server):
    """Test error handling when artifact is not found."""
    result = server._handle_trace("NONEXISTENT")
    assert "error" in result
    assert "not found" in result["error"]


def test_error_handling_link_source_not_found(server):
    """Test error handling when link source is not found."""
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})

    result = server._handle_propose_link({
        "source_id": "NONEXISTENT",
        "target_id": "A",
        "relationship_type": "implements",
        "rationale": "test",
    })

    assert "error" in result
    assert "not found" in result["error"]


def test_persistence(temp_trace_dir):
    """Test that events persist to disk."""
    # Create server and add artifact
    server1 = TraceabilityServer(temp_trace_dir)
    server1._handle_add_artifact({
        "artifact_id": "PERSIST-001",
        "artifact_type": "requirement",
    })

    # Create new server instance (reload from disk)
    server2 = TraceabilityServer(temp_trace_dir)

    # Verify artifact is loaded
    assert "PERSIST-001" in server2.graph.graph
