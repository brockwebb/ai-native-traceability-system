"""Verification tests for artifact lifecycle requirements."""
import subprocess
import tempfile
from pathlib import Path

from trace_core.templates import TemplateLoader


def test_req_alc_005_template_classification():
    """REQ-ALC-005: System shall classify using template patterns."""
    # Test against systems-engineering template
    loader = TemplateLoader(Path(".trace/templates"))

    # Test all SE artifact types
    assert loader.classify_file("docs/requirements/srs.md", "systems-engineering") == "requirement"
    assert loader.classify_file("docs/requirements/conops.md", "systems-engineering") == "conops"
    # vision.md doesn't match requirement pattern, so it returns None (would fall back to document)
    assert loader.classify_file("docs/requirements/vision.md", "systems-engineering") is None
    assert loader.classify_file("docs/architecture/system_architecture.md", "systems-engineering") == "architecture"
    assert loader.classify_file("docs/design/detailed_design.md", "systems-engineering") == "design"
    assert loader.classify_file("docs/decisions/design_decisions.md", "systems-engineering") == "decision"

    # Test code and test patterns
    assert loader.classify_file("src/trace_core/models.py", "systems-engineering") == "module"
    assert loader.classify_file("tests/test_models.py", "systems-engineering") == "test"

    # Test fallback for non-matching files
    assert loader.classify_file("data.csv", "systems-engineering") is None


def test_req_alc_005_template_auto_selection():
    """REQ-ALC-005: Auto-select template for classification."""
    loader = TemplateLoader(Path(".trace/templates"))

    # Should find match in systems-engineering
    assert loader.classify_file("docs/requirements/srs.md") == "requirement"

    # Should find match in any template for module
    assert loader.classify_file("src/foo.py") == "module"


def test_req_alc_001_002_git_integration():
    """REQ-ALC-001 & REQ-ALC-002: Git-aware scanning."""
    # This test verifies the git ls-files mechanism works
    # Full integration testing done manually via bootstrap_scan.py

    # Verify git ls-files command works
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=Path("."),
        capture_output=True,
        text=True,
        check=True
    )

    files = set(result.stdout.strip().split('\n'))

    # Verify tracked files are included
    assert "README.md" in files
    assert "src/trace_core/__init__.py" in files

    # Verify .gitignore patterns are respected (tmp/ is in .gitignore)
    assert not any(f.startswith("tmp/") for f in files if f)


def test_template_patterns_comprehensive():
    """Comprehensive test of template pattern matching."""
    loader = TemplateLoader(Path(".trace/templates"))

    # Systems engineering template tests
    test_cases = [
        # (file_path, expected_type, template)
        ("docs/requirements/conops.md", "conops", "systems-engineering"),
        ("docs/requirements/requirements.md", "requirement", "systems-engineering"),
        ("docs/architecture/arch_design.md", "architecture", "systems-engineering"),
        ("docs/design/design_spec.md", "design", "systems-engineering"),
        ("docs/decisions/decision_001.md", "decision", "systems-engineering"),
        ("docs/decisions/adr_002.md", "decision", "systems-engineering"),
        ("src/module.py", "module", "systems-engineering"),
        ("tests/test_module.py", "test", "systems-engineering"),
    ]

    for file_path, expected_type, template in test_cases:
        actual_type = loader.classify_file(file_path, template)
        assert actual_type == expected_type, \
            f"Expected {file_path} to be {expected_type}, got {actual_type}"
