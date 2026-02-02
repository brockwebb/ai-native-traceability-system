"""Tests for template loading and classification."""
import pytest
import tempfile
from pathlib import Path
from trace_core.templates import TemplateLoader


@pytest.fixture
def templates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        tdir = Path(tmpdir)

        # Create minimal test template
        # Note: More specific patterns (test) must come before generic ones (module)
        template = """
name: Test Template
artifact_types:
  - id: test
    file_patterns: ["**/test_*.py"]
  - id: module
    file_patterns: ["**/*.py"]
  - id: doc
    file_patterns: ["**/*.md"]
relationship_chains:
  - source_type: test
    target_type: module
    relationship: verifies
"""
        (tdir / "test-template.yaml").write_text(template)
        yield tdir


def test_list_templates(templates_dir):
    loader = TemplateLoader(templates_dir)
    templates = loader.list_templates()
    assert "test-template" in templates


def test_get_template(templates_dir):
    loader = TemplateLoader(templates_dir)
    t = loader.get_template("test-template")
    assert t["name"] == "Test Template"
    assert len(t["artifact_types"]) == 3


def test_classify_file(templates_dir):
    loader = TemplateLoader(templates_dir)

    assert loader.classify_file("src/foo.py", "test-template") == "module"
    assert loader.classify_file("tests/test_foo.py", "test-template") == "test"
    assert loader.classify_file("README.md", "test-template") == "doc"
    assert loader.classify_file("data.csv", "test-template") is None


def test_classify_file_auto(templates_dir):
    loader = TemplateLoader(templates_dir)
    # Without specifying template, should still find match
    assert loader.classify_file("src/bar.py") == "module"
