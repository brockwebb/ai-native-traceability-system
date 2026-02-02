"""MCP Server exposing traceability tools to Claude."""
import asyncio
import os
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
    TemplateLoader,
)


class TraceabilityServer:
    """MCP server wrapping the traceability system."""

    def __init__(self, trace_dir: str = ".trace"):
        self.trace_dir = Path(trace_dir)
        self.events_path = self.trace_dir / "events.jsonl"
        self._last_mtime = 0
        self._event_log = None
        self._graph = None
        self._queries = None
        self._template_loader = None
        self.server = Server("trace-server")
        self._load()
        self._register_tools()

    def _load(self):
        """Load or reload graph from events."""
        self._event_log = EventLog(str(self.trace_dir))
        self._event_log.init()
        self._graph = TraceGraph(self._event_log)
        self._graph.rebuild()
        self._template_loader = TemplateLoader(self.trace_dir / "templates")
        self._queries = TraceQueries(self._graph, self._template_loader)
        if self.events_path.exists():
            self._last_mtime = os.path.getmtime(self.events_path)

    def _ensure_fresh(self):
        """Reload if events file changed."""
        if self.events_path.exists():
            current_mtime = os.path.getmtime(self.events_path)
            if current_mtime > self._last_mtime:
                self._load()

    @property
    def graph(self):
        """Get graph, reloading if events changed."""
        self._ensure_fresh()
        return self._graph

    @property
    def event_log(self):
        """Get event log, reloading if events changed."""
        self._ensure_fresh()
        return self._event_log

    @property
    def queries(self):
        """Get queries, reloading if events changed."""
        self._ensure_fresh()
        return self._queries

    @property
    def template_loader(self):
        """Get template loader, reloading if events changed."""
        self._ensure_fresh()
        return self._template_loader

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
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags for discovery and search",
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
                Tool(
                    name="list_artifacts",
                    description="List all registered artifacts, optionally filtered by type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "artifact_type": {
                                "type": "string",
                                "description": "Optional artifact type filter (requirement, decision, module, function, test, document, issue)",
                            },
                        },
                    },
                ),
                Tool(
                    name="search_artifacts",
                    description="Search artifacts by name, path, type, or tags",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Optional substring to search in artifact IDs and file paths",
                            },
                            "artifact_type": {
                                "type": "string",
                                "description": "Optional artifact type filter",
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags to search for (matches if artifact has ANY of these tags)",
                            },
                        },
                    },
                ),
                Tool(
                    name="list_templates",
                    description="List available methodology templates",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_template",
                    description="Get a methodology template definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Template name (e.g., 'systems-engineering', 'agile', 'lightweight')",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="apply_template",
                    description="Scaffold expected relationships from a methodology template. Creates proposed links for all relationship_chains defined in template. Does NOT create artifacts — only relationships between existing artifacts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Template name to apply",
                            },
                        },
                        "required": ["name"],
                    },
                ),
                Tool(
                    name="classify_artifact",
                    description="Suggest artifact type for a file based on template patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to file (relative to repo root)",
                            },
                            "template": {
                                "type": "string",
                                "description": "Optional template name. If not provided, tries all templates.",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="health_check",
                    description="Validate trace data integrity. Checks for missing files, broken links, duplicate IDs, and invalid artifact types.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
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
                elif name == "list_artifacts":
                    result = self._handle_list_artifacts(arguments)
                elif name == "search_artifacts":
                    result = self._handle_search_artifacts(arguments)
                elif name == "list_templates":
                    result = self._handle_list_templates()
                elif name == "get_template":
                    result = self._handle_get_template(arguments)
                elif name == "apply_template":
                    result = self._handle_apply_template(arguments)
                elif name == "classify_artifact":
                    result = self._handle_classify_artifact(arguments)
                elif name == "health_check":
                    result = self._handle_health_check()
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
        if "tags" in args:
            payload["tags"] = args["tags"]

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

    def _handle_list_artifacts(self, args: dict) -> dict:
        """Handle list_artifacts tool call."""
        artifact_type = args.get("artifact_type")
        artifacts = self.queries.list_artifacts(artifact_type)

        return {
            "artifacts": artifacts,
            "count": len(artifacts),
        }

    def _handle_search_artifacts(self, args: dict) -> dict:
        """Handle search_artifacts tool call."""
        query = args.get("query")
        artifact_type = args.get("artifact_type")
        tags = args.get("tags")

        matches = self.queries.search_artifacts(
            query=query,
            artifact_type=artifact_type,
            tags=tags
        )

        return {
            "matches": matches,
            "count": len(matches),
        }

    def _handle_list_templates(self) -> dict:
        """Handle list_templates tool call."""
        templates = self.template_loader.list_templates()
        return {"templates": templates, "count": len(templates)}

    def _handle_get_template(self, args: dict) -> dict:
        """Handle get_template tool call."""
        template = self.template_loader.get_template(args["name"])
        if not template:
            return {"error": f"Template '{args['name']}' not found"}
        return {"template": template}

    def _handle_apply_template(self, args: dict) -> dict:
        """Handle apply_template tool call."""
        template = self.template_loader.get_template(args["name"])
        if not template:
            return {"error": f"Template '{args['name']}' not found"}

        chains = template.get("relationship_chains", [])
        proposed = []

        # Get existing artifacts by type
        artifacts_by_type = {}
        for node_id, data in self.graph.graph.nodes(data=True):
            atype = data.get("artifact_type", "unknown")
            if atype not in artifacts_by_type:
                artifacts_by_type[atype] = []
            artifacts_by_type[atype].append(node_id)

        # For each chain, propose links between matching artifacts
        for chain in chains:
            source_type = chain["source_type"]
            target_type = chain["target_type"]
            rel_type = chain["relationship"]

            sources = artifacts_by_type.get(source_type, [])
            targets = artifacts_by_type.get(target_type, [])

            for src in sources:
                for tgt in targets:
                    # Check if link already exists
                    if not self.graph.graph.has_edge(src, tgt):
                        # Create and append event
                        payload = {
                            "source_id": src,
                            "target_id": tgt,
                            "relationship_type": rel_type,
                        }
                        event = Event(
                            event_type=EventType.LINK_ADDED,
                            payload=payload,
                            actor="ai:template-scaffold",
                            state=State.PROPOSED,
                            rationale=f"Template '{args['name']}': {chain.get('description', 'expected relationship')}",
                        )
                        self.event_log.append(event)
                        self.graph._apply_event(event)
                        proposed.append({"source": src, "target": tgt, "relationship": rel_type})

        return {
            "template": args["name"],
            "proposed_links": proposed,
            "count": len(proposed)
        }

    def _handle_classify_artifact(self, args: dict) -> dict:
        """Handle classify_artifact tool call."""
        artifact_type = self.template_loader.classify_file(
            args["file_path"],
            args.get("template")
        )

        if artifact_type:
            return {
                "file_path": args["file_path"],
                "suggested_type": artifact_type,
                "template_used": args.get("template") or "auto"
            }
        else:
            return {
                "file_path": args["file_path"],
                "suggested_type": None,
                "message": "No matching pattern found"
            }

    def _handle_health_check(self) -> dict:
        """Handle health_check tool call."""
        # Determine repo root (parent of .trace directory)
        repo_root = self.trace_dir.parent
        return self.queries.health_check(repo_root)

    async def run(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def async_main():
    """Async main function for the MCP server."""
    # Get trace directory from environment or use default
    import os
    trace_dir = os.getenv("TRACE_DIR", ".trace")

    server = TraceabilityServer(trace_dir)
    await server.run()


def main():
    """Sync entry point wrapper for the MCP server."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
