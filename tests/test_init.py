"""Tests for REQ-INIT-001: One-Command Initialization."""
import json
import subprocess
from pathlib import Path
import pytest

from trace_core.init import TraceInitializer
from trace_core import resources


@pytest.fixture
def empty_repo(tmp_path):
    """Create an empty git repository."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_req_init_001_creates_trace_dir(empty_repo):
    """REQ-INIT-001: trace init creates .trace/ directory structure."""
    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_scan=True)

    assert result.success
    assert (empty_repo / ".trace").exists()
    assert (empty_repo / ".trace").is_dir()
    assert (empty_repo / ".trace" / "events.jsonl").exists()
    assert (empty_repo / ".trace" / "templates").exists()
    assert (empty_repo / ".trace" / "README.md").exists()


def test_req_init_001_detects_se_project(empty_repo):
    """REQ-INIT-001: Detects systems-engineering from docs/requirements/."""
    # Create SE directory structure
    (empty_repo / "docs" / "requirements").mkdir(parents=True)
    (empty_repo / "docs" / "requirements" / "srs.md").write_text("# Requirements\n")

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(template="auto", skip_scan=True)

    assert result.success
    assert result.template_used == "systems-engineering"


def test_req_init_001_detects_agile_project(empty_repo):
    """REQ-INIT-001: Detects agile from tests/ + src/ without SE docs."""
    # Create agile structure (tests + src, no SE docs)
    (empty_repo / "tests").mkdir()
    (empty_repo / "src").mkdir()
    (empty_repo / "tests" / "test_foo.py").write_text("# test\n")
    (empty_repo / "src" / "foo.py").write_text("# module\n")

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(template="auto", skip_scan=True)

    assert result.success
    assert result.template_used == "agile"


def test_req_init_001_detects_lightweight_project(empty_repo):
    """REQ-INIT-001: Falls back to lightweight for minimal projects."""
    # Minimal project - no clear signals
    (empty_repo / "README.md").write_text("# Project\n")

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(template="auto", skip_scan=True)

    assert result.success
    assert result.template_used == "lightweight"


def test_req_init_001_generates_mcp_json(empty_repo):
    """REQ-INIT-001: Generates valid .mcp.json with correct paths."""
    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_scan=True)

    assert result.success

    mcp_path = empty_repo / ".mcp.json"
    assert mcp_path.exists()

    # Validate JSON structure
    with open(mcp_path) as f:
        config = json.load(f)

    assert "mcpServers" in config
    assert "trace" in config["mcpServers"]
    assert "command" in config["mcpServers"]["trace"]
    assert "args" in config["mcpServers"]["trace"]
    assert "cwd" in config["mcpServers"]["trace"]
    assert "env" in config["mcpServers"]["trace"]

    # Check values
    assert config["mcpServers"]["trace"]["cwd"] == str(empty_repo)
    assert config["mcpServers"]["trace"]["env"]["TRACE_DIR"] == str(empty_repo / ".trace")


def test_req_init_001_copies_skill_file(empty_repo):
    """REQ-INIT-001: Copies skill file when .claude/ exists."""
    # Create .claude directory
    (empty_repo / ".claude").mkdir()

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_scan=True)

    assert result.success

    skill_path = empty_repo / ".claude" / "skills" / "traceability.md"
    assert skill_path.exists()

    # Verify content is from bundled resource
    content = skill_path.read_text()
    assert "Traceability Skill" in content
    assert "Auto-Capture Triggers" in content


def test_req_init_001_skips_skill_without_claude_dir(empty_repo):
    """REQ-INIT-001: Does not create skill if no .claude/ directory."""
    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_scan=True)

    assert result.success

    # Should not create .claude or skill file
    assert not (empty_repo / ".claude").exists()
    assert not (empty_repo / ".claude" / "skills" / "traceability.md").exists()


def test_req_init_001_runs_bootstrap(empty_repo):
    """REQ-INIT-001: Runs bootstrap scan and registers artifacts."""
    # Create some files
    (empty_repo / "README.md").write_text("# Test\n")
    (empty_repo / "src").mkdir()
    (empty_repo / "src" / "module.py").write_text("# code\n")

    # Add to git
    subprocess.run(["git", "add", "."], cwd=empty_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=empty_repo, check=True, capture_output=True)

    initializer = TraceInitializer(empty_repo)
    result = initializer.run()  # Don't skip scan

    assert result.success
    assert result.artifacts_found > 0

    # Verify events were written
    events_path = empty_repo / ".trace" / "events.jsonl"
    assert events_path.exists()

    event_count = sum(1 for _ in open(events_path))
    assert event_count > 0


def test_req_init_001_idempotent(empty_repo):
    """REQ-INIT-001: Running init twice doesn't break things."""
    initializer = TraceInitializer(empty_repo)

    # First run
    result1 = initializer.run(skip_scan=True)
    assert result1.success

    # Second run on same repo
    initializer2 = TraceInitializer(empty_repo)
    result2 = initializer2.run(skip_scan=True)
    assert result2.success

    # Should still have valid structure
    assert (empty_repo / ".trace").exists()
    assert (empty_repo / ".trace" / "events.jsonl").exists()
    assert (empty_repo / ".mcp.json").exists()


def test_req_init_001_dry_run(empty_repo):
    """REQ-INIT-001: Dry run shows actions without making changes."""
    initializer = TraceInitializer(empty_repo)
    result = initializer.run(dry_run=True)

    assert result.success

    # Should NOT create anything
    assert not (empty_repo / ".trace").exists()
    assert not (empty_repo / ".mcp.json").exists()

    # But should have logged messages
    assert len(result.messages) > 0


def test_req_init_001_respects_skip_flags(empty_repo):
    """REQ-INIT-001: Skip flags prevent respective actions."""
    # Create .claude to test skill skip
    (empty_repo / ".claude").mkdir()

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_mcp=True, skip_skill=True, skip_scan=True)

    assert result.success

    # .trace should exist
    assert (empty_repo / ".trace").exists()

    # But these should not
    assert not (empty_repo / ".mcp.json").exists()
    assert not (empty_repo / ".claude" / "skills" / "traceability.md").exists()


def test_req_init_001_uses_bundled_resources(empty_repo):
    """REQ-INIT-001: Templates load from installed package, not relative paths.

    Ensures trace init works when run from any project directory
    after pip install, without needing the source tree present.
    """
    initializer = TraceInitializer(empty_repo)
    result = initializer.run(skip_scan=True)

    assert result.success

    # Check templates were copied from bundled resources
    templates_dir = empty_repo / ".trace" / "templates"
    assert (templates_dir / "systems-engineering.yaml").exists()
    assert (templates_dir / "agile.yaml").exists()
    assert (templates_dir / "lightweight.yaml").exists()

    # Verify content matches bundled resources
    se_template = (templates_dir / "systems-engineering.yaml").read_text()
    assert "name: Systems Engineering" in se_template


def test_req_init_001_resources_list_templates():
    """REQ-INIT-001: Resource loading lists available templates."""
    templates = resources.list_templates()

    assert isinstance(templates, list)
    assert len(templates) == 3
    assert "systems-engineering" in templates
    assert "agile" in templates
    assert "lightweight" in templates


def test_req_init_001_resources_get_template():
    """REQ-INIT-001: Resource loading retrieves template content."""
    content = resources.get_template("systems-engineering")

    assert isinstance(content, str)
    assert "name: Systems Engineering" in content
    assert "artifact_types:" in content


def test_req_init_001_resources_get_skill_file():
    """REQ-INIT-001: Resource loading retrieves skill file content."""
    content = resources.get_skill_file()

    assert isinstance(content, str)
    assert "Traceability Skill" in content
    assert "Auto-Capture Triggers" in content


def test_req_init_001_explicit_template_selection(empty_repo):
    """REQ-INIT-001: Explicit template selection overrides auto-detection."""
    # Create SE structure but force lightweight
    (empty_repo / "docs" / "requirements").mkdir(parents=True)

    initializer = TraceInitializer(empty_repo)
    result = initializer.run(template="lightweight", skip_scan=True)

    assert result.success
    assert result.template_used == "lightweight"  # Should use explicit, not auto-detected


def test_req_init_001_warns_non_git_repo(tmp_path):
    """REQ-INIT-001: Warns when not a git repository."""
    # tmp_path is not a git repo
    initializer = TraceInitializer(tmp_path)
    result = initializer.run(skip_scan=True)

    assert result.success
    # Should have warning in messages
    assert any("not a git repository" in msg.lower() for msg in result.messages)


def test_req_init_001_cli_integration(empty_repo):
    """REQ-INIT-001: CLI command works end-to-end."""
    # Run trace init via subprocess
    result = subprocess.run(
        ["trace", "init", "--skip-scan", str(empty_repo)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert (empty_repo / ".trace").exists()
    assert (empty_repo / ".mcp.json").exists()
    assert "Initialization complete" in result.stdout


def test_req_init_001_status_command(empty_repo):
    """REQ-INIT-001: Status command shows initialization state."""
    # Initialize first
    initializer = TraceInitializer(empty_repo)
    initializer.run(skip_scan=True)

    # Check status via CLI
    result = subprocess.run(
        ["trace", "status", str(empty_repo)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Traceability initialized" in result.stdout or "initialized" in result.stdout.lower()


def test_req_init_001_status_not_initialized(empty_repo):
    """REQ-INIT-001: Status command reports when not initialized."""
    result = subprocess.run(
        ["trace", "status", str(empty_repo)],
        capture_output=True,
        text=True
    )

    assert result.returncode == 1
    assert "Not initialized" in result.stdout
