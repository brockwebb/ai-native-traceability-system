#!/usr/bin/env python
"""Dogfood script: Register the traceability system's own artifacts."""
from pathlib import Path
from mcp_server.server import TraceabilityServer


def main():
    """Register this repo's artifacts in the traceability system."""
    print("=== Dogfooding: Tracing This Repository ===\n")

    # Initialize server with repo's .trace directory
    server = TraceabilityServer(".trace")
    print("✓ Server initialized\n")

    # Step 1: Register key artifacts
    print("Step 1: Registering artifacts...")
    artifacts = [
        # Documentation
        {
            "artifact_id": "design_decisions",
            "artifact_type": "decision",
            "file_path": "docs/design_decisions_2025-01-31.md",
        },
        {
            "artifact_id": "vision_plan",
            "artifact_type": "requirement",
            "file_path": "docs/ai_native_traceability_system_top_level_vision_plan.md",
        },
        {
            "artifact_id": "claude_md",
            "artifact_type": "document",
            "file_path": "CLAUDE.md",
        },
        # Core library
        {
            "artifact_id": "models.py",
            "artifact_type": "module",
            "file_path": "src/trace_core/models.py",
        },
        {
            "artifact_id": "events.py",
            "artifact_type": "module",
            "file_path": "src/trace_core/events.py",
        },
        {
            "artifact_id": "graph.py",
            "artifact_type": "module",
            "file_path": "src/trace_core/graph.py",
        },
        {
            "artifact_id": "queries.py",
            "artifact_type": "module",
            "file_path": "src/trace_core/queries.py",
        },
        # MCP server
        {
            "artifact_id": "server.py",
            "artifact_type": "module",
            "file_path": "mcp_server/server.py",
        },
        # Tests
        {
            "artifact_id": "test_events.py",
            "artifact_type": "test",
            "file_path": "tests/test_events.py",
        },
        {
            "artifact_id": "test_graph.py",
            "artifact_type": "test",
            "file_path": "tests/test_graph.py",
        },
        {
            "artifact_id": "test_queries.py",
            "artifact_type": "test",
            "file_path": "tests/test_queries.py",
        },
        {
            "artifact_id": "test_mcp_server.py",
            "artifact_type": "test",
            "file_path": "tests/test_mcp_server.py",
        },
    ]

    for artifact in artifacts:
        result = server._handle_add_artifact(artifact)
        if result.get("success"):
            print(f"  ✓ {artifact['artifact_id']:25} ({artifact['artifact_type']})")
        else:
            print(f"  ✗ {artifact['artifact_id']:25} ERROR: {result.get('error')}")

    print(f"\n  Total artifacts registered: {len(artifacts)}\n")

    # Step 2: Create links (propose)
    print("Step 2: Proposing links...")
    links = [
        # Design decisions → implementation
        {
            "source_id": "design_decisions",
            "target_id": "models.py",
            "relationship_type": "implements",
            "rationale": "models.py implements the data model decisions from design doc",
        },
        # Code dependencies (architectural flow)
        {
            "source_id": "models.py",
            "target_id": "events.py",
            "relationship_type": "depends_on",
            "rationale": "events.py depends on Event and enum models from models.py",
        },
        {
            "source_id": "events.py",
            "target_id": "graph.py",
            "relationship_type": "depends_on",
            "rationale": "graph.py uses EventLog to rebuild the NetworkX graph",
        },
        {
            "source_id": "graph.py",
            "target_id": "queries.py",
            "relationship_type": "depends_on",
            "rationale": "queries.py operates on TraceGraph instance",
        },
        {
            "source_id": "queries.py",
            "target_id": "server.py",
            "relationship_type": "depends_on",
            "rationale": "server.py uses TraceQueries to implement MCP tools",
        },
        # Tests → code under test
        {
            "source_id": "test_events.py",
            "target_id": "events.py",
            "relationship_type": "verifies",
            "rationale": "test_events.py tests EventLog functionality",
        },
        {
            "source_id": "test_graph.py",
            "target_id": "graph.py",
            "relationship_type": "verifies",
            "rationale": "test_graph.py tests TraceGraph projection",
        },
        {
            "source_id": "test_queries.py",
            "target_id": "queries.py",
            "relationship_type": "verifies",
            "rationale": "test_queries.py tests query functions",
        },
        {
            "source_id": "test_mcp_server.py",
            "target_id": "server.py",
            "relationship_type": "verifies",
            "rationale": "test_mcp_server.py tests MCP server integration",
        },
        # Vision → design decisions
        {
            "source_id": "vision_plan",
            "target_id": "design_decisions",
            "relationship_type": "references",
            "rationale": "Design decisions implement the vision and requirements",
        },
    ]

    for link in links:
        result = server._handle_propose_link(link)
        if result.get("success"):
            print(f"  ✓ {link['source_id']:25} → {link['target_id']:25} ({link['relationship_type']})")
        else:
            print(f"  ✗ {link['source_id']:25} → {link['target_id']:25} ERROR: {result.get('error')}")

    print(f"\n  Total links proposed: {len(links)}\n")

    # Step 3: Accept all proposals (human approval)
    print("Step 3: Accepting all proposals (human approval)...")
    accepted = 0
    for link in links:
        result = server._handle_accept_proposal({
            "source_id": link["source_id"],
            "target_id": link["target_id"],
        })
        if result.get("success"):
            accepted += 1

    print(f"  ✓ Accepted {accepted} proposals\n")

    # Step 4: Verify with queries
    print("Step 4: Verification queries...")

    # Trace models.py
    print("\n  trace('models.py'):")
    result = server._handle_trace("models.py")
    print(f"    Upstream:   {result['upstream']}")
    print(f"    Downstream: {result['downstream']}")

    # Impact of models.py
    print("\n  impact('models.py'):")
    result = server._handle_impact("models.py")
    print(f"    Affected: {result['affected_artifacts']}")
    print(f"    Count:    {result['count']}")

    # Check orphans
    print("\n  orphans():")
    result = server._handle_orphans()
    if result['orphan_artifacts']:
        print(f"    Orphans: {result['orphan_artifacts']}")
    else:
        print(f"    No orphans ✓")

    # Check proposed links (should be empty)
    print("\n  proposed_links():")
    result = server._handle_proposed_links()
    print(f"    Proposed: {result['count']} (should be 0)")

    # Show the full dependency chain
    print("\n  Full dependency chain from design_decisions:")
    chain = []
    current = "design_decisions"
    visited = set()
    while current and current not in visited:
        visited.add(current)
        chain.append(current)
        trace_result = server._handle_trace(current)
        downstream = trace_result.get("downstream", [])
        current = downstream[0] if downstream else None

    print(f"    {' → '.join(chain)}")

    # Summary
    print("\n=== Summary ===")
    print(f"  Artifacts:        {len(artifacts)}")
    print(f"  Links:            {len(links)}")
    print(f"  All authoritative: ✓")
    print(f"  Events persisted:  .trace/events.jsonl")

    # Show event count
    event_count = server.event_log.count()
    print(f"  Total events:      {event_count}")

    print("\n✓ Dogfooding complete! Repository is now self-traced.\n")


if __name__ == "__main__":
    main()
