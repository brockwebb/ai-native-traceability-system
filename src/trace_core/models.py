"""Data models for traceability events and artifacts."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class ArtifactType(Enum):
    """Types of artifacts that can be traced."""
    REQUIREMENT = "requirement"
    DECISION = "decision"
    MODULE = "module"
    FUNCTION = "function"
    TEST = "test"
    DOCUMENT = "document"
    ISSUE = "issue"


class RelationshipType(Enum):
    """Types of relationships between artifacts."""
    IMPLEMENTS = "implements"      # code implements requirement
    DEPENDS_ON = "depends_on"      # A depends on B
    VERIFIES = "verifies"          # test verifies requirement
    SUPERSEDES = "supersedes"      # new decision supersedes old
    CONTAINS = "contains"          # parent contains child
    REFERENCES = "references"      # generic reference


class State(Enum):
    """Authority state of an event or relationship."""
    PROPOSED = "proposed"          # AI-generated, awaiting approval
    AUTHORITATIVE = "authoritative"  # Human-approved


class EventType(Enum):
    """Types of events in the trace log."""
    ARTIFACT_ADDED = "artifact_added"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_REMOVED = "artifact_removed"
    LINK_ADDED = "link_added"
    LINK_REMOVED = "link_removed"
    LINK_PROMOTED = "link_promoted"      # proposed -> authoritative
    LINK_REJECTED = "link_rejected"      # proposed -> rejected
    DECISION_LOGGED = "decision_logged"
    ANCHOR_REGISTERED = "anchor_registered"
    ANCHOR_STALE = "anchor_stale"        # content hash mismatch


@dataclass
class Event:
    """A single event in the trace log."""
    event_type: EventType
    payload: dict[str, Any]
    actor: str = "human"                 # human | ai:claude-code | ai:claude-desktop
    state: State = State.PROPOSED
    rationale: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize event to dictionary for JSON storage."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor": self.actor,
            "state": self.state.value,
            "payload": self.payload,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Deserialize event from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=EventType(data["event_type"]),
            actor=data["actor"],
            state=State(data["state"]),
            payload=data["payload"],
            rationale=data.get("rationale"),
        )
