#!/usr/bin/env python3
"""
Register documentation artifacts and create trace links.

This script registers the newly created user guide and reference documentation,
and links them to the code they document.
"""

from pathlib import Path
from mcp_server.server import TraceabilityServer

def main():
    # Initialize server with repo's .trace directory
    server = TraceabilityServer(".trace")

    print("Registering documentation artifacts...")

    # Define artifacts
    artifacts = [
        {
            "artifact_id": "docs/user-guide/quick-start.md",
            "artifact_type": "document",
            "file_path": "docs/user-guide/quick-start.md",
            "tags": ["documentation", "user-guide", "v0.3"],
        },
        {
            "artifact_id": "docs/user-guide/concepts.md",
            "artifact_type": "document",
            "file_path": "docs/user-guide/concepts.md",
            "tags": ["documentation", "user-guide", "concepts"],
        },
        {
            "artifact_id": "docs/user-guide/workflows.md",
            "artifact_type": "document",
            "file_path": "docs/user-guide/workflows.md",
            "tags": ["documentation", "user-guide", "workflows"],
        },
        {
            "artifact_id": "docs/reference/cli.md",
            "artifact_type": "document",
            "file_path": "docs/reference/cli.md",
            "tags": ["documentation", "reference", "cli"],
        },
        {
            "artifact_id": "docs/reference/mcp-tools.md",
            "artifact_type": "document",
            "file_path": "docs/reference/mcp-tools.md",
            "tags": ["documentation", "reference", "mcp"],
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
        # Link reference docs to implementations
        {
            "source_id": "docs/reference/mcp-tools.md",
            "target_id": "mcp_server/server.py",
            "relationship_type": "documents",
            "rationale": "MCP tools reference documents the server implementation",
        },
        {
            "source_id": "docs/reference/cli.md",
            "target_id": "src/trace_core/cli.py",
            "relationship_type": "documents",
            "rationale": "CLI reference documents the CLI implementation",
        },
        # Link user guide to v0.3 requirements
        {
            "source_id": "docs/user-guide/quick-start.md",
            "target_id": "docs/requirements/v0.3_requirements.md",
            "relationship_type": "documents",
            "rationale": "Quick start documents v0.3 user-facing features",
        },
        # Link workflows to automation tools
        {
            "source_id": "docs/user-guide/workflows.md",
            "target_id": "docs/requirements/v0.3_requirements.md",
            "relationship_type": "documents",
            "rationale": "Workflows document v0.3 automation features",
        },
        # Link concepts to core modules
        {
            "source_id": "docs/user-guide/concepts.md",
            "target_id": "src/trace_core/models.py",
            "relationship_type": "documents",
            "rationale": "Concepts document explains the data model implemented in models.py",
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
    print("\nDocumentation artifacts registered and links proposed.")
    print("Check proposed links with MCP tool: trace:proposed_links()")
    print("Accept proposals with: trace:accept_proposal(source_id, target_id)")

if __name__ == "__main__":
    main()
