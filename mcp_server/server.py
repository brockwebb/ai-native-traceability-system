"""MCP Server exposing traceability tools to Claude."""
# TODO: Implement MCP server
# Will expose: trace, impact, orphans, decisions, propose_link, accept_proposal
# See: https://modelcontextprotocol.io/docs/tools

from pathlib import Path

# Placeholder for MCP implementation
# from mcp import Server, Tool

from trace_core import EventLog, TraceGraph, TraceQueries


def create_server(trace_dir: str = ".trace"):
    """Create MCP server with traceability tools."""
    event_log = EventLog(trace_dir)
    event_log.init()

    graph = TraceGraph(event_log)
    graph.rebuild()

    queries = TraceQueries(graph)

    # TODO: Register MCP tools
    # - trace(artifact_id) -> upstream/downstream
    # - impact(artifact_id) -> transitive affected
    # - orphans() -> unlinked artifacts
    # - decisions() -> all decision records
    # - propose_link(source, target, rel_type, rationale)
    # - accept_proposal(source, target)

    return {
        "event_log": event_log,
        "graph": graph,
        "queries": queries,
    }
