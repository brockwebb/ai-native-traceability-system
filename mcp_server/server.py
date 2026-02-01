"""MCP Server exposing traceability tools to Claude."""
import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from trace_core import (
    Event,
    EventLog,
    EventType,
    RelationshipType,
    State,
    TraceGraph,
    TraceQueries,
)


class TraceabilityServer:
    """MCP server wrapping the traceability system."""

    def __init__(self, trace_dir: str = ".trace"):
        self.event_log = EventLog(trace_dir)
        self.event_log.init()
        self.graph = TraceGraph(self.event_log)
        self.graph.rebuild()
        self.queries = TraceQueries(self.graph)
        self.server = Server("trace-server")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all traceability tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            return [
                Tool(
                    name="trace",
                    description="Get upstream and downstream neighbors of an artifact",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "artifact_id": {
                                "type": "string",
                                "description": "The artifact ID to trace",
                            }
                        },
                        "required": ["artifact_id"],
                    },
                ),
                Tool(
                    name="impact",
                    description="Get all artifacts affected if this artifact changes (transitive downstream)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "artifact_id": {
                                "type": "string",
                                "description": "The artifact ID to analyze impact for",
                            }
                        },
                        "required": ["artifact_id"],
                    },
                ),
                Tool(
                    name="orphans",
                    description="Find all artifacts with no incoming or outgoing relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="decisions",
                    description="Get all decision records",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="proposed_links",
                    description="Get all links awaiting approval (proposed state)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="add_artifact",
                    description="Register a new artifact in the trace system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "artifact_id": {
                                "type": "string",
                                "description": "Unique ID for the artifact",
                            },
                            "artifact_type": {
                                "type": "string",
                                "description": "Type of artifact (requirement, decision, module, function, test, document, issue)",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Optional file path where artifact is located",
                            },
                            "line_start": {
                                "type": "integer",
                                "description": "Optional starting line number in file",
                            },
                            "content_hash": {
                                "type": "string",
                                "description": "Optional content hash for change detection",
                            },
                        },
                        "required": ["artifact_id", "artifact_type"],
                    },
                ),
                Tool(
                    name="propose_link",
                    description="Create a proposed link between two artifacts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                                "description": "Source artifact ID",
                            },
                            "target_id": {
                                "type": "string",
                                "description": "Target artifact ID",
                            },
                            "relationship_type": {
                                "type": "string",
                                "description": "Type of relationship (implements, depends_on, verifies, supersedes, contains, references)",
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Reasoning for this link",
                            },
                        },
                        "required": ["source_id", "target_id", "relationship_type", "rationale"],
                    },
                ),
                Tool(
                    name="accept_proposal",
                    description="Promote a proposed link to authoritative state",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "type": "string",
                                "description": "Source artifact ID",
                            },
                            "target_id": {
                                "type": "string",
                                "description": "Target artifact ID",
                            },
                        },
                        "required": ["source_id", "target_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "trace":
                    result = self._handle_trace(arguments["artifact_id"])
                elif name == "impact":
                    result = self._handle_impact(arguments["artifact_id"])
                elif name == "orphans":
                    result = self._handle_orphans()
                elif name == "decisions":
                    result = self._handle_decisions()
                elif name == "proposed_links":
                    result = self._handle_proposed_links()
                elif name == "add_artifact":
                    result = self._handle_add_artifact(arguments)
                elif name == "propose_link":
                    result = self._handle_propose_link(arguments)
                elif name == "accept_proposal":
                    result = self._handle_accept_proposal(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                # Format result as JSON string
                import json
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    def _handle_trace(self, artifact_id: str) -> dict:
        """Handle trace tool call."""
        if artifact_id not in self.graph.graph:
            return {"error": f"Artifact not found: {artifact_id}"}

        result = self.queries.trace(artifact_id)
        result["artifact_id"] = artifact_id
        return result

    def _handle_impact(self, artifact_id: str) -> dict:
        """Handle impact tool call."""
        if artifact_id not in self.graph.graph:
            return {"error": f"Artifact not found: {artifact_id}"}

        affected = self.queries.impact(artifact_id)
        return {
            "artifact_id": artifact_id,
            "affected_artifacts": affected,
            "count": len(affected),
        }

    def _handle_orphans(self) -> dict:
        """Handle orphans tool call."""
        orphans = self.queries.orphans()
        return {
            "orphan_artifacts": orphans,
            "count": len(orphans),
        }

    def _handle_decisions(self) -> dict:
        """Handle decisions tool call."""
        decisions = self.queries.decisions()
        return {
            "decisions": decisions,
            "count": len(decisions),
        }

    def _handle_proposed_links(self) -> dict:
        """Handle proposed_links tool call."""
        proposed = self.queries.proposed_links()
        # Format as list of dicts for easier reading
        links = [
            {
                "source": u,
                "target": v,
                "relationship_type": d.get("relationship_type"),
                "rationale": d.get("rationale"),
            }
            for u, v, d in proposed
        ]
        return {
            "proposed_links": links,
            "count": len(links),
        }

    def _handle_add_artifact(self, args: dict) -> dict:
        """Handle add_artifact tool call."""
        payload = {
            "artifact_id": args["artifact_id"],
            "artifact_type": args["artifact_type"],
        }

        # Add optional fields if present
        if "file_path" in args:
            payload["file_path"] = args["file_path"]
        if "line_start" in args:
            payload["line_start"] = args["line_start"]
        if "content_hash" in args:
            payload["content_hash"] = args["content_hash"]

        # Create and append event
        event = Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload=payload,
            actor="ai:claude-code",
            state=State.PROPOSED,
        )
        self.event_log.append(event)

        # Apply to graph
        self.graph._apply_event(event)

        return {
            "success": True,
            "artifact_id": args["artifact_id"],
            "state": "proposed",
        }

    def _handle_propose_link(self, args: dict) -> dict:
        """Handle propose_link tool call."""
        # Validate artifacts exist
        if args["source_id"] not in self.graph.graph:
            return {"error": f"Source artifact not found: {args['source_id']}"}
        if args["target_id"] not in self.graph.graph:
            return {"error": f"Target artifact not found: {args['target_id']}"}

        payload = {
            "source_id": args["source_id"],
            "target_id": args["target_id"],
            "relationship_type": args["relationship_type"],
        }

        event = Event(
            event_type=EventType.LINK_ADDED,
            payload=payload,
            actor="ai:claude-code",
            state=State.PROPOSED,
            rationale=args["rationale"],
        )
        self.event_log.append(event)

        # Apply to graph
        self.graph._apply_event(event)

        return {
            "success": True,
            "source": args["source_id"],
            "target": args["target_id"],
            "relationship_type": args["relationship_type"],
            "state": "proposed",
        }

    def _handle_accept_proposal(self, args: dict) -> dict:
        """Handle accept_proposal tool call."""
        # Verify link exists and is in proposed state
        if not self.graph.graph.has_edge(args["source_id"], args["target_id"]):
            return {"error": f"Link not found: {args['source_id']} -> {args['target_id']}"}

        edge_data = self.graph.graph.edges[args["source_id"], args["target_id"]]
        if edge_data.get("state") != State.PROPOSED.value:
            return {"error": f"Link is not in proposed state"}

        payload = {
            "source_id": args["source_id"],
            "target_id": args["target_id"],
        }

        event = Event(
            event_type=EventType.LINK_PROMOTED,
            payload=payload,
            actor="human",  # Acceptance is always human action
            state=State.AUTHORITATIVE,
        )
        self.event_log.append(event)

        # Apply to graph
        self.graph._apply_event(event)

        return {
            "success": True,
            "source": args["source_id"],
            "target": args["target_id"],
            "state": "authoritative",
        }

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for the MCP server."""
    # Get trace directory from environment or use default
    import os
    trace_dir = os.getenv("TRACE_DIR", ".trace")

    server = TraceabilityServer(trace_dir)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
