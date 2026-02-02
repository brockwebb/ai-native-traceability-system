"""Tests for REQ-CD-001: Git Sync Tool and REQ-ALC-003/004: File lifecycle detection."""
import subprocess
from pathlib import Path
import pytest

from trace_core import EventLog, Event, EventType, State, TraceGraph, TraceQueries, TemplateLoader


@pytest.fixture
def git_repo_setup(tmp_path):
    """Set up a git repository with trace system."""
    trace_dir = tmp_path / ".trace"
    trace_dir.mkdir()
    (trace_dir / "templates").mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)

    # Create initial files and commit
    (tmp_path / "file1.py").write_text("# file 1\n")
    (tmp_path / "file2.py").write_text("# file 2\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)

    # Create event log and graph
    event_log = EventLog(str(trace_dir))
    event_log.init()
    graph = TraceGraph(event_log)

    # Create template loader
    template_path = trace_dir / "templates" / "test-template.yaml"
    template_path.write_text("""
name: Test Template
artifact_types:
  - id: module
    name: Code Module
    file_patterns: ["**/*.py"]
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


def test_req_cd_001_detect_added_files(git_repo_setup):
    """REQ-CD-001: Detect files added to git but not traced."""
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # No artifacts registered yet, but files exist in git
    result = queries.sync_with_git(tmp_path)

    assert result["summary"]["added_count"] == 2
    assert len(result["added_files"]) == 2

    # Check file paths
    added_paths = [f["file_path"] for f in result["added_files"]]
    assert "file1.py" in added_paths
    assert "file2.py" in added_paths

    # Check suggested types
    for added_file in result["added_files"]:
        assert added_file["suggested_type"] == "module"


def test_req_alc_003_detect_deleted_files(git_repo_setup):
    """REQ-ALC-003: Detect files deleted from git but still traced."""
    event_log = git_repo_setup["event_log"]
    graph = git_repo_setup["graph"]
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # Register artifacts for both files
    for i, filename in enumerate(["file1.py", "file2.py"], 1):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
                "file_path": filename
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Delete file1.py from git
    (tmp_path / "file1.py").unlink()
    subprocess.run(["git", "add", "-u"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "delete file1"], cwd=tmp_path, check=True, capture_output=True)

    # Run sync
    result = queries.sync_with_git(tmp_path)

    assert result["summary"]["deleted_count"] == 1
    assert len(result["deleted_files"]) == 1
    assert result["deleted_files"][0]["file_path"] == "file1.py"
    assert result["deleted_files"][0]["artifact_id"] == "test-001"


def test_req_alc_004_detect_renamed_files(git_repo_setup):
    """REQ-ALC-004: Detect files renamed in git using rename detection."""
    event_log = git_repo_setup["event_log"]
    graph = git_repo_setup["graph"]
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # Register artifact for file1.py
    event = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "file1.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event)
    graph._apply_event(event)

    # Rename file1.py to renamed.py using git mv
    subprocess.run(["git", "mv", "file1.py", "renamed.py"], cwd=tmp_path, check=True, capture_output=True)

    # Run sync (before committing, so diff shows the rename)
    result = queries.sync_with_git(tmp_path)

    assert result["summary"]["renamed_count"] == 1
    assert len(result["renamed_files"]) == 1
    assert result["renamed_files"][0]["artifact_id"] == "test-001"
    assert result["renamed_files"][0]["old_path"] == "file1.py"
    assert result["renamed_files"][0]["new_path"] == "renamed.py"


def test_req_cd_001_no_changes(git_repo_setup):
    """REQ-CD-001: Sync reports no changes when trace and git are in sync."""
    event_log = git_repo_setup["event_log"]
    graph = git_repo_setup["graph"]
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # Register artifacts for both files
    for i, filename in enumerate(["file1.py", "file2.py"], 1):
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={
                "artifact_id": f"test-{i:03d}",
                "artifact_type": "module",
                "file_path": filename
            },
            actor="test",
            state=State.AUTHORITATIVE
        )
        event_log.append(event)
        graph._apply_event(event)

    # Run sync
    result = queries.sync_with_git(tmp_path)

    assert result["summary"]["added_count"] == 0
    assert result["summary"]["deleted_count"] == 0
    assert result["summary"]["renamed_count"] == 0
    assert len(result["added_files"]) == 0
    assert len(result["deleted_files"]) == 0
    assert len(result["renamed_files"]) == 0


def test_req_cd_001_multiple_changes(git_repo_setup):
    """REQ-CD-001: Sync detects multiple types of changes simultaneously."""
    event_log = git_repo_setup["event_log"]
    graph = git_repo_setup["graph"]
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # Register artifact for file1.py only
    event = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-001",
            "artifact_type": "module",
            "file_path": "file1.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event)
    graph._apply_event(event)

    # Register artifact for a file that will be deleted
    event2 = Event(
        event_type=EventType.ARTIFACT_ADDED,
        payload={
            "artifact_id": "test-002",
            "artifact_type": "module",
            "file_path": "deleted.py"
        },
        actor="test",
        state=State.AUTHORITATIVE
    )
    event_log.append(event2)
    graph._apply_event(event2)

    # Create deleted.py and commit it
    (tmp_path / "deleted.py").write_text("# to be deleted\n")
    subprocess.run(["git", "add", "deleted.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add deleted.py"], cwd=tmp_path, check=True, capture_output=True)

    # Now delete it
    (tmp_path / "deleted.py").unlink()
    subprocess.run(["git", "add", "-u"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "delete file"], cwd=tmp_path, check=True, capture_output=True)

    # Run sync
    result = queries.sync_with_git(tmp_path)

    # file2.py is added (in git, not traced)
    assert result["summary"]["added_count"] >= 1
    added_paths = [f["file_path"] for f in result["added_files"]]
    assert "file2.py" in added_paths

    # deleted.py is deleted (traced, not in git)
    assert result["summary"]["deleted_count"] == 1
    assert result["deleted_files"][0]["file_path"] == "deleted.py"


def test_req_cd_001_structured_report(git_repo_setup):
    """REQ-CD-001: Sync returns structured report."""
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    result = queries.sync_with_git(tmp_path)

    # Verify report structure
    assert "added_files" in result
    assert "deleted_files" in result
    assert "renamed_files" in result
    assert "summary" in result

    # Verify summary structure
    assert "added_count" in result["summary"]
    assert "deleted_count" in result["summary"]
    assert "renamed_count" in result["summary"]

    assert isinstance(result["added_files"], list)
    assert isinstance(result["deleted_files"], list)
    assert isinstance(result["renamed_files"], list)


def test_req_cd_001_artifact_type_suggestion(git_repo_setup):
    """REQ-CD-001: Sync suggests artifact types for added files."""
    queries = git_repo_setup["queries"]
    tmp_path = git_repo_setup["tmp_path"]

    # Create files of different types
    (tmp_path / "test.md").write_text("# Test\n")
    subprocess.run(["git", "add", "test.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add md"], cwd=tmp_path, check=True, capture_output=True)

    result = queries.sync_with_git(tmp_path)

    # Find the .md file in added files
    md_files = [f for f in result["added_files"] if f["file_path"] == "test.md"]
    assert len(md_files) == 1

    # Should have a suggested type (even if just "document" as fallback)
    assert "suggested_type" in md_files[0]
    assert md_files[0]["suggested_type"] is not None
