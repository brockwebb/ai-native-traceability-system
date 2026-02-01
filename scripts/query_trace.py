#!/usr/bin/env python
"""Quick script to query the repository's self-trace."""
import json
from mcp_server.server import TraceabilityServer


def print_json(data):
    """Pretty print JSON."""
    print(json.dumps(data, indent=2))


def main():
    """Query the self-trace."""
    server = TraceabilityServer(".trace")

    print("=== Repository Traceability Queries ===\n")

    # Show all artifacts
    print("1. All artifacts in the graph:")
    artifacts = list(server.graph.graph.nodes())
    for i, artifact in enumerate(sorted(artifacts), 1):
        print(f"   {i:2}. {artifact}")

    print(f"\n   Total: {len(artifacts)} artifacts\n")

    # Show dependency chain
    print("2. Core library dependency chain:")
    chain = ["models.py", "events.py", "graph.py", "queries.py", "server.py"]
    for i, module in enumerate(chain):
        indent = "   " * i
        arrow = " └─> " if i > 0 else "   "
        print(f"{indent}{arrow}{module}")

    # Impact of changing design decisions
    print("\n3. Impact of changing 'design_decisions':")
    result = server._handle_impact("design_decisions")
    print(f"   Affected artifacts: {result['count']}")
    for artifact in sorted(result['affected_artifacts']):
        print(f"     - {artifact}")

    # Test coverage
    print("\n4. Test coverage (tests → code):")
    test_links = [
        ("test_events.py", "events.py"),
        ("test_graph.py", "graph.py"),
        ("test_queries.py", "queries.py"),
        ("test_mcp_server.py", "server.py"),
    ]
    for test, code in test_links:
        has_link = server.graph.graph.has_edge(test, code)
        status = "✓" if has_link else "✗"
        print(f"   {status} {test} → {code}")

    # Find what implements requirements
    print("\n5. What implements 'design_decisions'?")
    result = server._handle_trace("design_decisions")
    print(f"   Downstream implementations: {result['downstream']}")

    # Check for orphans
    print("\n6. Orphaned artifacts:")
    result = server._handle_orphans()
    if result['orphan_artifacts']:
        for orphan in result['orphan_artifacts']:
            print(f"   - {orphan}")
    else:
        print("   None (all artifacts are connected)")

    # Authority state
    print("\n7. Authority state:")
    result = server._handle_proposed_links()
    print(f"   Proposed links awaiting approval: {result['count']}")
    total_links = server.graph.graph.number_of_edges()
    authoritative = total_links - result['count']
    print(f"   Authoritative links: {authoritative}")

    print("\n✓ All queries completed successfully!\n")


if __name__ == "__main__":
    main()
