#!/usr/bin/env python3
"""
Register v0.4 reports implementation artifacts and create trace links.

This script registers the reports.py module, test files, and creates
links to requirements.
"""

from pathlib import Path
from mcp_server.server import TraceabilityServer

def main():
    # Initialize server with repo's .trace directory
    server = TraceabilityServer(".trace")

    print("Registering v0.4 reports implementation artifacts...")

    # Define artifacts
    artifacts = [
        {
            "artifact_id": "src/trace_core/reports.py",
            "artifact_type": "module",
            "file_path": "src/trace_core/reports.py",
            "tags": ["v0.4", "reports", "core"],
        },
        {
            "artifact_id": "tests/test_reports.py",
            "artifact_type": "test",
            "file_path": "tests/test_reports.py",
            "tags": ["v0.4", "reports", "tests"],
        },
        {
            "artifact_id": "tests/conftest.py",
            "artifact_type": "test",
            "file_path": "tests/conftest.py",
            "tags": ["test-fixtures", "shared"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_mermaid",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_dependency_map",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_coverage_report",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_rtm",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_impact_report",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
        },
        {
            "artifact_id": "mcp_server/server.py#export_decision_log",
            "artifact_type": "function",
            "file_path": "mcp_server/server.py",
            "tags": ["v0.4", "mcp-tool", "reports"],
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
        # Reports module implements all v0.4 requirements
        {
            "source_id": "src/trace_core/reports.py",
            "target_id": "docs/requirements/v0.4_requirements.md",
            "relationship_type": "implements",
            "rationale": "ReportGenerator class implements all 6 v0.4 requirements",
        },
        # Tests verify reports module
        {
            "source_id": "tests/test_reports.py",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "verifies",
            "rationale": "Comprehensive tests for all 6 report generators",
        },
        # MCP tools depend on reports module
        {
            "source_id": "mcp_server/server.py#export_mermaid",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_mermaid()",
        },
        {
            "source_id": "mcp_server/server.py#export_dependency_map",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_dependency_map()",
        },
        {
            "source_id": "mcp_server/server.py#export_coverage_report",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_coverage_report()",
        },
        {
            "source_id": "mcp_server/server.py#export_rtm",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_rtm()",
        },
        {
            "source_id": "mcp_server/server.py#export_impact_report",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_impact_report()",
        },
        {
            "source_id": "mcp_server/server.py#export_decision_log",
            "target_id": "src/trace_core/reports.py",
            "relationship_type": "depends_on",
            "rationale": "MCP tool calls ReportGenerator.export_decision_log()",
        },
        # conftest.py provides fixtures for test_reports.py
        {
            "source_id": "tests/conftest.py",
            "target_id": "tests/test_reports.py",
            "relationship_type": "supports",
            "rationale": "Provides pytest fixtures for report testing",
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
    print("\nv0.4 reports implementation artifacts registered and links proposed.")
    print("Check proposed links with MCP tool: trace:proposed_links()")
    print("Accept proposals with: trace:accept_proposal(source_id, target_id)")
    print("Or accept all with: trace:accept_all_proposed()")

if __name__ == "__main__":
    main()
