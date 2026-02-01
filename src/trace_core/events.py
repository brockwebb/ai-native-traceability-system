"""Event log management - append-only JSONL storage."""
import json
from pathlib import Path
from typing import Iterator

from .models import Event


class EventLog:
    """Manages the append-only event log (.trace/events.jsonl)."""

    def __init__(self, trace_dir: Path | str = ".trace"):
        self.trace_dir = Path(trace_dir)
        self.events_file = self.trace_dir / "events.jsonl"

    def init(self) -> None:
        """Initialize trace directory if it doesn't exist."""
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        if not self.events_file.exists():
            self.events_file.touch()

    def append(self, event: Event) -> None:
        """Append a single event to the log."""
        with self.events_file.open("a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def read_all(self) -> list[Event]:
        """Read all events from the log."""
        return list(self.iter_events())

    def iter_events(self) -> Iterator[Event]:
        """Iterate over events without loading all into memory."""
        if not self.events_file.exists():
            return
        with self.events_file.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Event.from_dict(json.loads(line))

    def count(self) -> int:
        """Count total events in the log."""
        if not self.events_file.exists():
            return 0
        with self.events_file.open() as f:
            return sum(1 for line in f if line.strip())
