#!/usr/bin/env python
"""Manual test script for MCP server.

This script demonstrates how to use the MCP server to:
1. Add artifacts
2. Create links between them
3. Query the graph
4. Accept proposals
"""
import tempfile
from mcp_server.server import TraceabilityServer


def main():
    """Run a manual test of the MCP server."""
    print("=== MCP Server Manual Test ===\n")

    # Create server with temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using trace directory: {tmpdir}\n")
        server = TraceabilityServer(tmpdir)

        # 1. Add artifacts
        print("1. Adding artifacts...")
        artifacts = [
            {"artifact_id": "FR-1", "artifact_type": "requirement"},
            {"artifact_id": "SYS-001", "artifact_type": "module"},
            {"artifact_id": "func_process", "artifact_type": "function"},
            {"artifact_id": "test_process", "artifact_type": "test"},
        ]

        for artifact in artifacts:
            result = server._handle_add_artifact(artifact)
            print(f"   Added: {artifact['artifact_id']} - {result}")

        # 2. Propose links
        print("\n2. Proposing links...")
        links = [
            {
                "source_id": "FR-1",
                "target_id": "SYS-001",
                "relationship_type": "implements",
                "rationale": "SYS-001 implements requirement FR-1",
            },
            {
                "source_id": "SYS-001",
                "target_id": "func_process",
                "relationship_type": "contains",
                "rationale": "SYS-001 contains function func_process",
            },
            {
                "source_id": "func_process",
                "target_id": "test_process",
                "relationship_type": "verifies",
                "rationale": "test_process verifies func_process",
            },
        ]

        for link in links:
            result = server._handle_propose_link(link)
            print(f"   Link: {link['source_id']} -> {link['target_id']} - {result['success']}")

        # 3. Query proposed links
        print("\n3. Querying proposed links...")
        result = server._handle_proposed_links()
        print(f"   Found {result['count']} proposed links:")
        for link in result['proposed_links']:
            print(f"     {link['source']} -> {link['target']} ({link['relationship_type']})")

        # 4. Trace artifacts
        print("\n4. Tracing SYS-001...")
        result = server._handle_trace("SYS-001")
        print(f"   Upstream: {result['upstream']}")
        print(f"   Downstream: {result['downstream']}")

        # 5. Impact analysis
        print("\n5. Impact analysis for FR-1...")
        result = server._handle_impact("FR-1")
        print(f"   Affected artifacts: {result['affected_artifacts']}")
        print(f"   Total count: {result['count']}")

        # 6. Accept a proposal
        print("\n6. Accepting proposal FR-1 -> SYS-001...")
        result = server._handle_accept_proposal({
            "source_id": "FR-1",
            "target_id": "SYS-001",
        })
        print(f"   Accepted: {result['success']} - State: {result['state']}")

        # 7. Check proposed links again
        print("\n7. Querying proposed links after acceptance...")
        result = server._handle_proposed_links()
        print(f"   Found {result['count']} proposed links (should be 2 now)")

        # 8. Check orphans
        print("\n8. Checking for orphans...")
        # Add an orphan artifact
        server._handle_add_artifact({"artifact_id": "ORPHAN-001", "artifact_type": "requirement"})
        result = server._handle_orphans()
        print(f"   Orphan artifacts: {result['orphan_artifacts']}")

        # 9. Check events persisted to disk
        print("\n9. Verifying persistence...")
        event_count = server.event_log.count()
        print(f"   Total events in log: {event_count}")

        print("\n=== Test Complete ===")
        print("All operations completed successfully!")


if __name__ == "__main__":
    main()
