"""Accept all proposed links."""
from trace_core import TraceGraph, EventLog, Event, EventType, State
from pathlib import Path

trace_dir = Path(".trace")
event_log = EventLog(str(trace_dir))
event_log.init()
graph = TraceGraph(event_log)
graph.rebuild()

# Get all proposed links
proposed = []
for u, v, data in graph.graph.edges(data=True):
    if data.get("state") == State.PROPOSED.value:
        proposed.append({"source": u, "target": v, "data": data})

print(f"Accepting {len(proposed)} proposed links...")

for link in proposed:
    # Create promotion event
    payload = {
        "source_id": link["source"],
        "target_id": link["target"],
    }

    event = Event(
        event_type=EventType.LINK_PROMOTED,
        payload=payload,
        actor="human",  # Acceptance is always human action
        state=State.AUTHORITATIVE,
    )
    event_log.append(event)
    graph._apply_event(event)

    print(f"  ✓ {link['source']} -> {link['target']}")

print("Done.")
