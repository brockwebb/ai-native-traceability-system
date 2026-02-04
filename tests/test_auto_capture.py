"""Tests for REQ-AUTO-001 and REQ-IMPACT-001: Automated capture tools."""
import pytest
from pathlib import Path

from trace_core import EventLog, TraceGraph, TraceQueries, TemplateLoader


@pytest.fixture
def trace_env(tmp_path):
    """Set up trace environment with templates."""
    trace_dir = tmp_path / ".trace"
    trace_dir.mkdir()
    templates_dir = trace_dir / "templates"
    templates_dir.mkdir()

    # Create minimal template (order matters - specific before general)
    (templates_dir / "test.yaml").write_text("""
name: Test Template
artifact_types:
  - id: test
    name: Test
    file_patterns:
      - "tests/**/*.py"
      - "**/test_*.py"
  - id: module
    name: Module
    file_patterns:
      - "src/**/*.py"
  - id: document
    name: Document
    file_patterns:
      - "docs/**/*.md"
      - "**/*.md"
""")

    event_log = EventLog(str(trace_dir))
    event_log.init()
    graph = TraceGraph(event_log)
    template_loader = TemplateLoader(templates_dir)
    queries = TraceQueries(graph, template_loader)

    return {
        "queries": queries,
        "graph": graph,
        "event_log": event_log,
        "tmp_path": tmp_path
    }


# ============ REQ-AUTO-001 Tests ============

def test_req_auto_001_register_file_classifies_module(trace_env):
    """REQ-AUTO-001: register_file() correctly classifies src/*.py as module."""
    queries = trace_env["queries"]

    result = queries.register_file("src/trace_core/validators.py")

    assert result["success"] is True
    assert result["artifact_type"] == "module"
    assert result["already_exists"] is False


def test_req_auto_001_register_file_classifies_test(trace_env):
    """REQ-AUTO-001: register_file() correctly classifies tests/*.py as test."""
    queries = trace_env["queries"]

    result = queries.register_file("tests/test_validators.py")

    assert result["success"] is True
    assert result["artifact_type"] == "test"


def test_req_auto_001_register_file_classifies_doc(trace_env):
    """REQ-AUTO-001: register_file() correctly classifies docs/*.md as document."""
    queries = trace_env["queries"]

    result = queries.register_file("docs/design/overview.md")

    assert result["success"] is True
    assert result["artifact_type"] == "document"


def test_req_auto_001_register_file_idempotent(trace_env):
    """REQ-AUTO-001: register_file() is idempotent - second call returns already_exists."""
    queries = trace_env["queries"]

    result1 = queries.register_file("src/new_module.py")
    result2 = queries.register_file("src/new_module.py")

    assert result1["already_exists"] is False
    assert result2["already_exists"] is True
    assert result2["success"] is True


def test_req_auto_001_register_file_adds_to_graph(trace_env):
    """REQ-AUTO-001: register_file() actually adds artifact to graph."""
    queries = trace_env["queries"]
    graph = trace_env["graph"]

    queries.register_file("src/new_module.py")

    assert "src/new_module.py" in graph.graph.nodes()


def test_req_auto_001_register_file_unknown_defaults_document(trace_env):
    """REQ-AUTO-001: register_file() defaults to 'document' for unknown patterns."""
    queries = trace_env["queries"]

    result = queries.register_file("random/unknown/file.xyz")

    assert result["artifact_type"] == "document"


# ============ REQ-IMPACT-001 Tests ============

def test_req_impact_001_check_impact_no_downstream(trace_env):
    """REQ-IMPACT-001: check_impact() returns empty downstream for isolated artifact."""
    queries = trace_env["queries"]

    queries.register_file("src/isolated.py")
    result = queries.check_impact("src/isolated.py")

    assert result["count"] == 0
    assert result["exceeds_threshold"] is False
    assert result["warning"] is None


def test_req_impact_001_check_impact_below_threshold(trace_env):
    """REQ-IMPACT-001: check_impact() does not warn when below threshold."""
    queries = trace_env["queries"]
    graph = trace_env["graph"]

    # Create artifact with 2 downstream (below default threshold of 3)
    queries.register_file("src/base.py")
    queries.register_file("src/child1.py")
    queries.register_file("src/child2.py")

    # Manually add edges (normally done via propose_link)
    # Note: NetworkX directed edges go source -> target
    # For downstream calculation, we need edges pointing FROM base TO children
    graph.graph.add_edge("src/base.py", "src/child1.py", relationship_type="implements")
    graph.graph.add_edge("src/base.py", "src/child2.py", relationship_type="implements")

    result = queries.check_impact("src/base.py")

    assert result["count"] == 2
    assert result["exceeds_threshold"] is False
    assert result["warning"] is None


def test_req_impact_001_check_impact_exceeds_threshold(trace_env):
    """REQ-IMPACT-001: check_impact() warns when exceeding threshold."""
    queries = trace_env["queries"]
    graph = trace_env["graph"]

    # Create artifact with 5 downstream (above default threshold of 3)
    queries.register_file("src/core.py")
    for i in range(5):
        queries.register_file(f"src/dependent{i}.py")
        graph.graph.add_edge("src/core.py", f"src/dependent{i}.py", relationship_type="implements")

    result = queries.check_impact("src/core.py")

    assert result["count"] == 5
    assert result["exceeds_threshold"] is True
    assert result["warning"] is not None
    assert "⚠️" in result["warning"]
    assert "5 downstream" in result["warning"]


def test_req_impact_001_check_impact_custom_threshold(trace_env):
    """REQ-IMPACT-001: check_impact() respects custom threshold."""
    queries = trace_env["queries"]
    graph = trace_env["graph"]

    queries.register_file("src/base.py")
    queries.register_file("src/child.py")
    graph.graph.add_edge("src/base.py", "src/child.py", relationship_type="implements")

    # With threshold=0, even 1 downstream should warn
    result = queries.check_impact("src/base.py", threshold=0)

    assert result["exceeds_threshold"] is True
    assert result["warning"] is not None


def test_req_impact_001_check_impact_transitive(trace_env):
    """REQ-IMPACT-001: check_impact() counts transitive downstream."""
    queries = trace_env["queries"]
    graph = trace_env["graph"]

    # Chain: a -> b -> c -> d (a has 3 transitive downstream)
    for name in ["a", "b", "c", "d"]:
        queries.register_file(f"src/{name}.py")

    graph.graph.add_edge("src/a.py", "src/b.py", relationship_type="implements")
    graph.graph.add_edge("src/b.py", "src/c.py", relationship_type="implements")
    graph.graph.add_edge("src/c.py", "src/d.py", relationship_type="implements")

    result = queries.check_impact("src/a.py")

    # b, c, d are all downstream of a
    assert result["count"] == 3


def test_req_impact_001_check_impact_nonexistent_artifact(trace_env):
    """REQ-IMPACT-001: check_impact() handles non-existent artifact gracefully."""
    queries = trace_env["queries"]

    result = queries.check_impact("does/not/exist.py")

    assert result["count"] == 0
    assert result["exceeds_threshold"] is False
