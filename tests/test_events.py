"""Tests for event log functionality."""
import tempfile
from pathlib import Path

import pytest

from trace_core import Event, EventLog
from trace_core.models import EventType, State


def test_event_log_init():
    """Test event log initialization creates directory and file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / ".trace"
        log = EventLog(trace_dir)
        log.init()

        assert trace_dir.exists()
        assert (trace_dir / "events.jsonl").exists()


def test_event_append_and_read():
    """Test appending and reading events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log = EventLog(Path(tmpdir) / ".trace")
        log.init()

        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "REQ-001", "artifact_type": "requirement"},
            actor="human",
            state=State.AUTHORITATIVE,
        )
        log.append(event)

        events = log.read_all()
        assert len(events) == 1
        assert events[0].payload["artifact_id"] == "REQ-001"


def test_event_serialization():
    """Test event round-trip through JSON."""
    event = Event(
        event_type=EventType.LINK_ADDED,
        payload={"source_id": "REQ-001", "target_id": "MOD-001", "relationship_type": "implements"},
        actor="ai:claude-code",
        state=State.PROPOSED,
        rationale="Code in module implements requirement",
    )

    data = event.to_dict()
    restored = Event.from_dict(data)

    assert restored.event_type == event.event_type
    assert restored.payload == event.payload
    assert restored.actor == event.actor
    assert restored.state == event.state
    assert restored.rationale == event.rationale
