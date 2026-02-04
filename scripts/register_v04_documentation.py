#!/usr/bin/env python3
"""
Register v0.4 documentation artifacts and create trace links.

This script registers the updated and new documentation files for v0.4.
"""

from pathlib import Path
from mcp_server.server import TraceabilityServer

def main():
    # Initialize server with repo's .trace directory
    server = TraceabilityServer(".trace")

    print("Registering v0.4 documentation artifacts...")

    # Define artifacts
    artifacts = [
        {
            "artifact_id": "docs/user-guide/automatic-capture.md",
            "artifact_type": "document",
            "file_path": "docs/user-guide/automatic-capture.md",
            "tags": ["documentation", "user-guide", "v0.3", "automation"],
        },
        {
            "artifact_id": "docs/user-guide/reports-and-queries.md",
            "artifact_type": "document",
            "file_path": "docs/user-guide/reports-and-queries.md",
            "tags": ["documentation", "user-guide", "v0.4", "reports"],
        },
        {
            "artifact_id": "docs/reference/mcp-tools.md#v0.4-update",
            "artifact_type": "document",
            "file_path": "docs/reference/mcp-tools.md",
            "tags": ["documentation", "reference", "mcp", "updated"],
        },
        {
            "artifact_id": "mcp_server/README.md#v0.4-update",
            "artifact_type": "document",
            "file_path": "mcp_server/README.md",
            "tags": ["documentation", "mcp", "updated"],
        },
        {
            "artifact_id": "README.md#v0.4-update",
            "artifact_type": "document",
            "file_path": "README.md",
            "tags": ["documentation", "readme", "updated"],
        },
    ]

    # Register artifacts
    for artifact in artifacts:
        result = server._handle_add_artifact(artifact)
        if result.get("success"):
            print(f"  ✓ {artifact['artifact_id']}")
        else:
            print(f"  ✗ {artifact['artifact_id']} ERROR: {result.get('error')}")

    print(f"\n  Total artifacts registered: {len(artifacts)}\n")

    # Define links
    print("Proposing trace links...")
    links = [
        # Link user guide docs to requirements
        {
            "source_id": "docs/user-guide/automatic-capture.md",
            "target_id": "docs/requirements/v0.3_requirements.md",
            "relationship_type": "documents",
            "rationale": "Documents v0.3 automation features",
        },
        {
            "source_id": "docs/user-guide/reports-and-queries.md",
            "target_id": "docs/requirements/v0.4_requirements.md",
            "relationship_type": "documents",
            "rationale": "Documents v0.4 report features",
        },
        # Link reference docs to implementation
        {
            "source_id": "docs/reference/mcp-tools.md#v0.4-update",
            "target_id": "mcp_server/server.py",
            "relationship_type": "documents",
            "rationale": "Documents all 28 MCP tools including v0.4 reports",
        },
        {
            "source_id": "docs/reference/mcp-tools.md#v0.4-update",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "documents",
            "rationale": "Documents report generation methods",
        },
        # Link README updates to project status
        {
            "source_id": "README.md#v0.4-update",
            "target_id": "docs/requirements/v0.4_requirements.md",
            "relationship_type": "documents",
            "rationale": "Reflects v0.4 completion in project README",
        },
        {
            "source_id": "mcp_server/README.md#v0.4-update",
            "target_id": "docs/requirements/v0.4_requirements.md",
            "relationship_type": "documents",
            "rationale": "Documents v0.4 MCP tools in server README",
        },
    ]

    # Propose links
    for link in links:
        result = server._handle_propose_link(link)
        if result.get("success"):
            print(f"  ✓ {link['source_id']} --{link['relationship_type']}--> {link['target_id']}")
        else:
            print(f"  ✗ {link['source_id']} → {link['target_id']} ERROR: {result.get('error')}")

    print(f"\n  Total links proposed: {len(links)}")

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print("\nv0.4 documentation artifacts registered and links proposed.")
    print("Check proposed links with MCP tool: trace:proposed_links()")
    print("Accept proposals with: trace:accept_proposal(source_id, target_id)")
    print("Or accept all with: trace:accept_all_proposed()")

if __name__ == "__main__":
    main()
