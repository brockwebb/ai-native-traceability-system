"""Tests for artifact discovery features."""
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


def test_add_artifact_with_tags(server):
    """Test adding an artifact with tags."""
    result = server._handle_add_artifact({
        "artifact_id": "roadmap",
        "artifact_type": "document",
        "file_path": "docs/roadmap.md",
        "tags": ["planning", "future", "vision"],
    })

    assert result["success"] is True
    assert result["artifact_id"] == "roadmap"

    # Verify tags are stored
    artifact = server.graph.get_artifact("roadmap")
    assert artifact is not None
    assert "tags" in artifact
    assert set(artifact["tags"]) == {"planning", "future", "vision"}


def test_add_artifact_without_tags(server):
    """Test adding an artifact without tags (backward compatible)."""
    result = server._handle_add_artifact({
        "artifact_id": "test-file",
        "artifact_type": "test",
        "file_path": "tests/test_foo.py",
    })

    assert result["success"] is True

    # Should work fine without tags
    artifact = server.graph.get_artifact("test-file")
    assert artifact is not None
    assert artifact.get("tags") is None or artifact.get("tags") == []


def test_list_artifacts_all(server):
    """Test listing all artifacts."""
    # Add several artifacts
    server._handle_add_artifact({"artifact_id": "A", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "B", "artifact_type": "module"})
    server._handle_add_artifact({"artifact_id": "C", "artifact_type": "test"})

    result = server._handle_list_artifacts({})

    assert result["count"] == 3
    assert len(result["artifacts"]) == 3

    ids = {a["artifact_id"] for a in result["artifacts"]}
    assert ids == {"A", "B", "C"}


def test_list_artifacts_filtered_by_type(server):
    """Test listing artifacts filtered by type."""
    # Add artifacts of different types
    server._handle_add_artifact({"artifact_id": "req1", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "req2", "artifact_type": "requirement"})
    server._handle_add_artifact({"artifact_id": "mod1", "artifact_type": "module"})
    server._handle_add_artifact({"artifact_id": "test1", "artifact_type": "test"})

    # Filter by requirement
    result = server._handle_list_artifacts({"artifact_type": "requirement"})

    assert result["count"] == 2
    ids = {a["artifact_id"] for a in result["artifacts"]}
    assert ids == {"req1", "req2"}


def test_search_artifacts_by_query_substring(server):
    """Test searching artifacts by substring in ID."""
    # Add artifacts
    server._handle_add_artifact({
        "artifact_id": "user-authentication",
        "artifact_type": "requirement",
    })
    server._handle_add_artifact({
        "artifact_id": "user-profile",
        "artifact_type": "requirement",
    })
    server._handle_add_artifact({
        "artifact_id": "payment-gateway",
        "artifact_type": "requirement",
    })

    # Search for "user"
    result = server._handle_search_artifacts({"query": "user"})

    assert result["count"] == 2
    ids = {a["artifact_id"] for a in result["matches"]}
    assert ids == {"user-authentication", "user-profile"}


def test_search_artifacts_by_file_path(server):
    """Test searching artifacts by substring in file path."""
    # Add artifacts with file paths
    server._handle_add_artifact({
        "artifact_id": "A",
        "artifact_type": "module",
        "file_path": "src/auth/login.py",
    })
    server._handle_add_artifact({
        "artifact_id": "B",
        "artifact_type": "module",
        "file_path": "src/auth/register.py",
    })
    server._handle_add_artifact({
        "artifact_id": "C",
        "artifact_type": "module",
        "file_path": "src/payment/stripe.py",
    })

    # Search for "auth"
    result = server._handle_search_artifacts({"query": "auth"})

    assert result["count"] == 2
    ids = {a["artifact_id"] for a in result["matches"]}
    assert ids == {"A", "B"}


def test_search_artifacts_by_tags(server):
    """Test searching artifacts by tags."""
    # Add artifacts with tags
    server._handle_add_artifact({
        "artifact_id": "roadmap",
        "artifact_type": "document",
        "tags": ["planning", "future"],
    })
    server._handle_add_artifact({
        "artifact_id": "sprint-plan",
        "artifact_type": "document",
        "tags": ["planning", "current"],
    })
    server._handle_add_artifact({
        "artifact_id": "tech-debt",
        "artifact_type": "document",
        "tags": ["maintenance"],
    })

    # Search for "planning" tag
    result = server._handle_search_artifacts({"tags": ["planning"]})

    assert result["count"] == 2
    ids = {a["artifact_id"] for a in result["matches"]}
    assert ids == {"roadmap", "sprint-plan"}


def test_search_artifacts_by_multiple_tags(server):
    """Test searching artifacts with multiple tags (OR logic)."""
    # Add artifacts
    server._handle_add_artifact({
        "artifact_id": "A",
        "artifact_type": "document",
        "tags": ["frontend"],
    })
    server._handle_add_artifact({
        "artifact_id": "B",
        "artifact_type": "document",
        "tags": ["backend"],
    })
    server._handle_add_artifact({
        "artifact_id": "C",
        "artifact_type": "document",
        "tags": ["database"],
    })

    # Search for frontend OR backend
    result = server._handle_search_artifacts({"tags": ["frontend", "backend"]})

    assert result["count"] == 2
    ids = {a["artifact_id"] for a in result["matches"]}
    assert ids == {"A", "B"}


def test_search_artifacts_combined_filters(server):
    """Test searching with multiple filters combined."""
    # Add artifacts
    server._handle_add_artifact({
        "artifact_id": "design-doc",
        "artifact_type": "document",
        "file_path": "docs/design.md",
        "tags": ["planning"],
    })
    server._handle_add_artifact({
        "artifact_id": "design-code",
        "artifact_type": "module",
        "file_path": "src/design.py",
        "tags": ["implementation"],
    })
    server._handle_add_artifact({
        "artifact_id": "other-doc",
        "artifact_type": "document",
        "file_path": "docs/other.md",
        "tags": ["maintenance"],
    })

    # Search: query="design" AND type="document"
    result = server._handle_search_artifacts({
        "query": "design",
        "artifact_type": "document",
    })

    assert result["count"] == 1
    assert result["matches"][0]["artifact_id"] == "design-doc"


def test_search_artifacts_case_insensitive(server):
    """Test that search is case-insensitive."""
    server._handle_add_artifact({
        "artifact_id": "UserAuth",
        "artifact_type": "module",
    })

    # Search with different case
    result = server._handle_search_artifacts({"query": "userauth"})
    assert result["count"] == 1

    result = server._handle_search_artifacts({"query": "USERAUTH"})
    assert result["count"] == 1

    result = server._handle_search_artifacts({"query": "UserAuth"})
    assert result["count"] == 1


def test_tags_persist_through_reload(server, temp_trace_dir):
    """Test that tags persist through event log save/reload cycle."""
    # Add artifact with tags
    server._handle_add_artifact({
        "artifact_id": "persistent",
        "artifact_type": "document",
        "tags": ["tag1", "tag2"],
    })

    # Create new server instance (reload from disk)
    server2 = TraceabilityServer(temp_trace_dir)

    # Verify tags are still there
    artifact = server2.graph.get_artifact("persistent")
    assert artifact is not None
    assert set(artifact["tags"]) == {"tag1", "tag2"}


def test_search_artifacts_no_matches(server):
    """Test search with no matches returns empty result."""
    server._handle_add_artifact({
        "artifact_id": "foo",
        "artifact_type": "module",
    })

    result = server._handle_search_artifacts({"query": "nonexistent"})

    assert result["count"] == 0
    assert result["matches"] == []


def test_list_artifacts_empty(server):
    """Test listing artifacts when none exist."""
    result = server._handle_list_artifacts({})

    assert result["count"] == 0
    assert result["artifacts"] == []
