"""Tests for REQ-INFER-001: Relationship inference from imports."""
import pytest
from pathlib import Path

from trace_core import EventLog, TraceGraph, TraceQueries, TemplateLoader


@pytest.fixture
def trace_env_with_files(tmp_path):
    """Set up trace environment with actual files to parse."""
    trace_dir = tmp_path / ".trace"
    trace_dir.mkdir()
    templates_dir = trace_dir / "templates"
    templates_dir.mkdir()

    # Create template
    (templates_dir / "test.yaml").write_text("""
name: Test Template
artifact_types:
  - id: module
    name: Module
    file_patterns:
      - "**/*.py"
  - id: document
    name: Document
    file_patterns:
      - "**/*.md"
""")

    event_log = EventLog(str(trace_dir))
    event_log.init()
    graph = TraceGraph(event_log)
    template_loader = TemplateLoader(templates_dir)
    queries = TraceQueries(graph, template_loader)

    # Create src directory structure
    (tmp_path / "src" / "trace_core").mkdir(parents=True)
    (tmp_path / "docs").mkdir()

    return {
        "queries": queries,
        "graph": graph,
        "event_log": event_log,
        "tmp_path": tmp_path,
        "repo_root": tmp_path
    }


# ============ Python Import Tests ============

def test_req_infer_001_detects_python_import(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() detects Python imports."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create a Python file with imports
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("""
import os
import sys
from trace_core import models
""")

    result = queries.infer_dependencies("src/test_module.py", repo_root=tmp_path)

    assert result["file_path"] == "src/test_module.py"
    assert isinstance(result["dependencies"], list)
    # Should detect trace_core.models import (others are external)


def test_req_infer_001_maps_import_to_artifact(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() maps import to traced artifact."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]
    graph = trace_env_with_files["graph"]

    # Create the dependency file
    models_file = tmp_path / "src" / "trace_core" / "models.py"
    models_file.write_text("# models module\n")

    # Register it as an artifact
    queries.register_file("src/trace_core/models.py")

    # Create a file that imports it
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("""
from trace_core import models
""")

    result = queries.infer_dependencies("src/test_module.py", repo_root=tmp_path)

    assert len(result["dependencies"]) > 0
    # Find the dependency
    deps = [d for d in result["dependencies"] if "models" in d["rationale"]]
    assert len(deps) > 0
    assert deps[0]["target"] == "src/trace_core/models.py"
    assert deps[0]["relationship_type"] == "depends_on"


def test_req_infer_001_skips_external_imports(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() ignores external library imports."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create a file with only external imports
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("""
import os
import sys
import json
from pathlib import Path
""")

    result = queries.infer_dependencies("src/test_module.py", repo_root=tmp_path)

    # Should have no dependencies (all external)
    assert len(result["dependencies"]) == 0
    assert result["skipped_count"] > 0


def test_req_infer_001_handles_from_import(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() handles 'from x import y' syntax."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create the dependency
    models_file = tmp_path / "src" / "trace_core" / "models.py"
    models_file.write_text("# models\n")
    queries.register_file("src/trace_core/models.py")

    # Create file with from...import
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("""
from trace_core.models import Event
from trace_core import models
""")

    result = queries.infer_dependencies("src/test_module.py", repo_root=tmp_path)

    # Should detect the trace_core.models import
    assert len(result["dependencies"]) > 0


def test_req_infer_001_auto_propose_creates_links(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies(auto_propose=True) creates proposed links."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]
    graph = trace_env_with_files["graph"]

    # Create dependency
    models_file = tmp_path / "src" / "trace_core" / "models.py"
    models_file.write_text("# models\n")
    queries.register_file("src/trace_core/models.py")

    # Create dependent file
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("from trace_core import models\n")
    queries.register_file("src/test_module.py")

    # Infer with auto_propose
    result = queries.infer_dependencies(
        "src/test_module.py",
        repo_root=tmp_path,
        auto_propose=True
    )

    assert result["proposed_count"] > 0

    # Verify link was created in graph
    assert graph.graph.has_edge("src/test_module.py", "src/trace_core/models.py")


# ============ Markdown Link Tests ============

def test_req_infer_001_detects_markdown_links(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() detects Markdown links."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create a Markdown file with links
    doc_file = tmp_path / "docs" / "index.md"
    doc_file.write_text("""
# Documentation

See [other doc](other.md) for details.
Also check [README](../README.md).
""")

    result = queries.infer_dependencies("docs/index.md", repo_root=tmp_path)

    assert result["file_path"] == "docs/index.md"
    assert isinstance(result["dependencies"], list)


def test_req_infer_001_maps_relative_links(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() maps relative Markdown links to artifacts."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create target document
    other_doc = tmp_path / "docs" / "other.md"
    other_doc.write_text("# Other\n")
    queries.register_file("docs/other.md")

    # Create document with link
    doc_file = tmp_path / "docs" / "index.md"
    doc_file.write_text("""
# Index

See [other doc](other.md) for details.
""")

    result = queries.infer_dependencies("docs/index.md", repo_root=tmp_path)

    # Should find the link to docs/other.md
    assert len(result["dependencies"]) > 0
    assert result["dependencies"][0]["target"] == "docs/other.md"
    assert result["dependencies"][0]["relationship_type"] == "references"


def test_req_infer_001_ignores_external_urls(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() ignores http/https URLs."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create Markdown with external links
    doc_file = tmp_path / "docs" / "index.md"
    doc_file.write_text("""
# Index

See [Google](https://google.com) and [GitHub](http://github.com).
""")

    result = queries.infer_dependencies("docs/index.md", repo_root=tmp_path)

    # Should have no dependencies (all external)
    assert len(result["dependencies"]) == 0


# ============ Integration Tests ============

def test_req_infer_001_returns_structured_result(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() returns properly structured result."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    # Create a simple Python file
    test_file = tmp_path / "src" / "test.py"
    test_file.write_text("import os\n")

    result = queries.infer_dependencies("src/test.py", repo_root=tmp_path)

    # Verify structure
    assert "file_path" in result
    assert "dependencies" in result
    assert "proposed_count" in result
    assert "skipped_count" in result

    assert isinstance(result["dependencies"], list)
    assert isinstance(result["proposed_count"], int)
    assert isinstance(result["skipped_count"], int)


def test_req_infer_001_dry_run_no_side_effects(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies(auto_propose=False) has no side effects."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]
    graph = trace_env_with_files["graph"]

    # Create dependency
    models_file = tmp_path / "src" / "trace_core" / "models.py"
    models_file.write_text("# models\n")
    queries.register_file("src/trace_core/models.py")

    # Create dependent file
    test_file = tmp_path / "src" / "test_module.py"
    test_file.write_text("from trace_core import models\n")
    queries.register_file("src/test_module.py")

    # Count edges before
    edges_before = len(list(graph.graph.edges()))

    # Infer WITHOUT auto_propose (dry run)
    result = queries.infer_dependencies(
        "src/test_module.py",
        repo_root=tmp_path,
        auto_propose=False
    )

    # Count edges after
    edges_after = len(list(graph.graph.edges()))

    # Should be no change in graph
    assert edges_before == edges_after
    assert result["proposed_count"] == 0
    assert len(result["dependencies"]) > 0  # But dependencies were detected


def test_req_infer_001_file_not_found(trace_env_with_files):
    """REQ-INFER-001: infer_dependencies() handles non-existent files gracefully."""
    tmp_path = trace_env_with_files["tmp_path"]
    queries = trace_env_with_files["queries"]

    result = queries.infer_dependencies("does/not/exist.py", repo_root=tmp_path)

    assert "error" in result
    assert result["proposed_count"] == 0
