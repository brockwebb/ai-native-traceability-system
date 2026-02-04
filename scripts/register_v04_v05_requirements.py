#!/usr/bin/env python3
"""
Register v0.4 and v0.5 requirements documents and propose trace links.

This script registers the newly created requirements documents and creates
the appropriate trace relationships as specified in the task.
"""

from pathlib import Path
from mcp_server.server import TraceabilityServer

def main():
    # Initialize server with repo's .trace directory
    server = TraceabilityServer(".trace")

    print("Registering v0.4 and v0.5 requirements documents...")

    # Define artifacts
    artifacts = [
        {
            "artifact_id": "docs/requirements/v0.4_requirements.md",
            "artifact_type": "requirement",
            "file_path": "docs/requirements/v0.4_requirements.md",
            "tags": ["v0.4", "planning"],
        },
        {
            "artifact_id": "docs/requirements/v0.5_requirements.md",
            "artifact_type": "requirement",
            "file_path": "docs/requirements/v0.5_requirements.md",
            "tags": ["v0.5", "planning"],
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
        {
            "source_id": "docs/requirements/v0.4_requirements.md",
            "target_id": "docs/roadmap.md",
            "relationship_type": "derives_from",
            "rationale": "v0.4 requirements derived from roadmap",
        },
        {
            "source_id": "docs/requirements/v0.5_requirements.md",
            "target_id": "docs/roadmap.md",
            "relationship_type": "derives_from",
            "rationale": "v0.5 requirements derived from roadmap",
        },
        {
            "source_id": "docs/requirements/v0.5_requirements.md",
            "target_id": "docs/requirements/v0.4_requirements.md",
            "relationship_type": "depends_on",
            "rationale": "v0.5 depends on v0.4 infrastructure (reports feed drift detection)",
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
    print("\nArtifacts registered and links proposed.")
    print("Check proposed links with MCP tool: trace:proposed_links()")
    print("Accept proposals with: trace:accept_proposal(proposal_id)")

if __name__ == "__main__":
    main()
