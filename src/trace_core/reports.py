"""Report generation for traceability data."""
from typing import Optional
import json
from .graph import TraceGraph


class ReportGenerator:
    """Generate reports from trace graph."""

    def __init__(self, graph: TraceGraph):
        self.graph = graph

    # === REQ-EXPORT-MERMAID-001: Mermaid Export ===

    def export_mermaid(
        self,
        root: Optional[str] = None,
        depth: Optional[int] = None,
        direction: str = "both",  # upstream, downstream, both
        artifact_types: Optional[list[str]] = None,
        relationship_types: Optional[list[str]] = None,
    ) -> str:
        """Export graph subset as Mermaid diagram."""
        lines = ["flowchart TD"]

        # Get subgraph (all nodes if no root)
        if root:
            nodes = self._get_subgraph(root, depth, direction)
        else:
            nodes = list(self.graph.graph.nodes())

        # Filter by artifact type
        if artifact_types:
            nodes = [n for n in nodes if self.graph.graph.nodes[n].get("artifact_type") in artifact_types]

        # Group by type for subgraphs
        by_type = {}
        for node in nodes:
            atype = self.graph.graph.nodes[node].get("artifact_type", "unknown")
            by_type.setdefault(atype, []).append(node)

        # Emit subgraphs
        for atype, type_nodes in by_type.items():
            lines.append(f"    subgraph {atype}s")
            for node in type_nodes:
                safe_id = self._mermaid_safe_id(node)
                lines.append(f"        {safe_id}[{node}]")
            lines.append("    end")

        # Emit edges
        for u, v, data in self.graph.graph.edges(data=True):
            if u in nodes and v in nodes:
                rel = data.get("relationship_type", "links")
                if relationship_types and rel not in relationship_types:
                    continue
                u_safe = self._mermaid_safe_id(u)
                v_safe = self._mermaid_safe_id(v)
                lines.append(f"    {u_safe} -->|{rel}| {v_safe}")

        return "\n".join(lines)

    def _mermaid_safe_id(self, node_id: str) -> str:
        """Convert artifact ID to valid Mermaid node ID."""
        # Replace problematic chars: /, ., -, spaces
        return node_id.replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")

    def _get_subgraph(self, root: str, depth: Optional[int], direction: str) -> list[str]:
        """Get nodes within depth of root."""
        nodes = {root}
        current = {root}

        for _ in range(depth or 10):  # default max depth
            next_level = set()
            for node in current:
                if direction in ("downstream", "both"):
                    next_level.update(self.graph.graph.successors(node))
                if direction in ("upstream", "both"):
                    next_level.update(self.graph.graph.predecessors(node))
            if not next_level - nodes:
                break
            nodes.update(next_level)
            current = next_level

        return list(nodes)

    # === REQ-DEP-001: Dependency Map ===

    def export_dependency_map(
        self,
        root: Optional[str] = None,
        depth: Optional[int] = None,
        format: str = "mermaid",  # mermaid, dot, json
        artifact_types: Optional[list[str]] = None,
        relationship_types: Optional[list[str]] = None,
    ) -> str:
        """Export dependency map in various formats."""
        if format == "mermaid":
            return self.export_mermaid(root, depth, "both", artifact_types, relationship_types)
        elif format == "dot":
            return self._export_dot(root, depth, artifact_types, relationship_types)
        elif format == "json":
            return self._export_json(root, depth, artifact_types, relationship_types)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _export_dot(self, root, depth, artifact_types, relationship_types) -> str:
        """Export as Graphviz DOT format."""
        lines = ["digraph G {", "    rankdir=TB;"]

        nodes = self._get_subgraph(root, depth, "both") if root else list(self.graph.graph.nodes())

        if artifact_types:
            nodes = [n for n in nodes if self.graph.graph.nodes[n].get("artifact_type") in artifact_types]

        for node in nodes:
            safe = node.replace('"', '\\"')
            lines.append(f'    "{safe}" [label="{safe}", shape=box];')

        for u, v, data in self.graph.graph.edges(data=True):
            if u in nodes and v in nodes:
                rel = data.get("relationship_type", "")
                if relationship_types and rel not in relationship_types:
                    continue
                u_safe = u.replace('"', '\\"')
                v_safe = v.replace('"', '\\"')
                lines.append(f'    "{u_safe}" -> "{v_safe}" [label="{rel}"];')

        lines.append("}")
        return "\n".join(lines)

    def _export_json(self, root, depth, artifact_types, relationship_types) -> str:
        """Export as JSON for custom visualization."""
        nodes = self._get_subgraph(root, depth, "both") if root else list(self.graph.graph.nodes())

        if artifact_types:
            nodes = [n for n in nodes if self.graph.graph.nodes[n].get("artifact_type") in artifact_types]

        result = {
            "nodes": [],
            "edges": []
        }

        for node in nodes:
            data = dict(self.graph.graph.nodes[node])
            data["id"] = node
            result["nodes"].append(data)

        for u, v, data in self.graph.graph.edges(data=True):
            if u in nodes and v in nodes:
                rel = data.get("relationship_type", "")
                if relationship_types and rel not in relationship_types:
                    continue
                result["edges"].append({
                    "source": u,
                    "target": v,
                    "relationship_type": rel,
                    "state": data.get("state")
                })

        return json.dumps(result, indent=2)

    # === REQ-COV-001: Coverage Report ===

    def export_coverage_report(self, format: str = "md") -> str:
        """
        Report traceability gaps:
        1. Orphan requirements (no implements)
        2. Untested modules (no verifies)
        3. Undocumented decisions
        4. Pending approvals
        """
        # Get artifacts by type
        requirements = [n for n, d in self.graph.graph.nodes(data=True)
                       if d.get("artifact_type") == "requirement"]
        modules = [n for n, d in self.graph.graph.nodes(data=True)
                  if d.get("artifact_type") == "module"]
        decisions = [n for n, d in self.graph.graph.nodes(data=True)
                    if d.get("artifact_type") == "decision"]

        # Find orphan requirements (nothing implements them)
        orphan_reqs = []
        for req in requirements:
            implementers = [u for u, v, d in self.graph.graph.in_edges(req, data=True)
                           if d.get("relationship_type") == "implements"]
            if not implementers:
                orphan_reqs.append(req)

        # Find untested modules (nothing verifies them)
        untested = []
        for mod in modules:
            verifiers = [u for u, v, d in self.graph.graph.in_edges(mod, data=True)
                        if d.get("relationship_type") == "verifies"]
            if not verifiers:
                untested.append(mod)

        # Find undocumented decisions (not linked to anything)
        undocumented = []
        for dec in decisions:
            links = list(self.graph.graph.successors(dec)) + list(self.graph.graph.predecessors(dec))
            if not links:
                undocumented.append(dec)

        # Pending approvals
        pending = [(u, v) for u, v, d in self.graph.graph.edges(data=True)
                   if d.get("state") == "proposed"]

        result = {
            "orphan_requirements": orphan_reqs,
            "untested_modules": untested,
            "undocumented_decisions": undocumented,
            "pending_approvals": len(pending),
            "summary": {
                "total_requirements": len(requirements),
                "orphan_count": len(orphan_reqs),
                "total_modules": len(modules),
                "untested_count": len(untested),
                "total_decisions": len(decisions),
                "undocumented_count": len(undocumented)
            }
        }

        if format == "json":
            return json.dumps(result, indent=2)

        # Markdown format
        lines = ["# Coverage Report", ""]

        lines.append("## Summary")
        lines.append(f"- Requirements: {len(orphan_reqs)}/{len(requirements)} orphaned")
        lines.append(f"- Modules: {len(untested)}/{len(modules)} untested")
        lines.append(f"- Decisions: {len(undocumented)}/{len(decisions)} undocumented")
        lines.append(f"- Pending approvals: {len(pending)}")
        lines.append("")

        if orphan_reqs:
            lines.append("## Orphan Requirements (no implementation)")
            for req in orphan_reqs:
                lines.append(f"- {req}")
            lines.append("")

        if untested:
            lines.append("## Untested Modules")
            for mod in untested:
                lines.append(f"- {mod}")
            lines.append("")

        if undocumented:
            lines.append("## Undocumented Decisions")
            for dec in undocumented:
                lines.append(f"- {dec}")
            lines.append("")

        return "\n".join(lines)

    # === REQ-RTM-001: Requirements Traceability Matrix ===

    def export_rtm(self, format: str = "md") -> str:
        """
        Requirements Traceability Matrix.

        | Requirement | Implementations | Tests | Status |
        |-------------|-----------------|-------|--------|
        | REQ-001     | auth.py         | test_auth.py | ✅ Traced |
        | REQ-002     | -               | -     | ❌ Orphan |
        """
        requirements = [n for n, d in self.graph.graph.nodes(data=True)
                       if d.get("artifact_type") == "requirement"]

        rows = []
        for req in sorted(requirements):
            # Find implementations (things that implement this requirement)
            impls = [u for u, v, d in self.graph.graph.in_edges(req, data=True)
                    if d.get("relationship_type") == "implements"]

            # Find tests that verify implementations
            tests = []
            for impl in impls:
                impl_tests = [u for u, v, d in self.graph.graph.in_edges(impl, data=True)
                             if d.get("relationship_type") == "verifies"]
                tests.extend(impl_tests)

            # Also find tests that directly verify the requirement
            direct_tests = [u for u, v, d in self.graph.graph.in_edges(req, data=True)
                           if d.get("relationship_type") == "verifies"]
            tests.extend(direct_tests)
            tests = list(set(tests))  # dedupe

            # Determine status
            if impls and tests:
                status = "✅ Fully Traced"
            elif impls:
                status = "⚠️ Untested"
            elif tests:
                status = "⚠️ No Implementation"
            else:
                status = "❌ Orphan"

            rows.append({
                "requirement": req,
                "implementations": impls,
                "tests": tests,
                "status": status
            })

        if format == "json":
            return json.dumps(rows, indent=2)

        if format == "csv":
            lines = ["Requirement,Implementations,Tests,Status"]
            for row in rows:
                impls = ";".join(row["implementations"]) or "-"
                tests = ";".join(row["tests"]) or "-"
                # Strip emoji for CSV
                status = row["status"].split(" ", 1)[1] if " " in row["status"] else row["status"]
                lines.append(f'"{row["requirement"]}","{impls}","{tests}","{status}"')
            return "\n".join(lines)

        # Markdown table
        lines = ["# Requirements Traceability Matrix", ""]
        lines.append("| Requirement | Implementations | Tests | Status |")
        lines.append("|-------------|-----------------|-------|--------|")

        for row in rows:
            impls = ", ".join(row["implementations"]) or "-"
            tests = ", ".join(row["tests"]) or "-"
            lines.append(f"| {row['requirement']} | {impls} | {tests} | {row['status']} |")

        return "\n".join(lines)

    # === REQ-IMPACT-RPT-001: Impact Report ===

    def export_impact_report(self, artifact_ids: list[str], format: str = "md") -> str:
        """Impact analysis for change management."""
        all_affected = {}

        for artifact_id in artifact_ids:
            if artifact_id not in self.graph.graph:
                continue

            # Direct (1 hop)
            direct = list(self.graph.graph.successors(artifact_id))

            # Transitive (full cascade)
            transitive = self._transitive_downstream(artifact_id)

            all_affected[artifact_id] = {
                "direct": direct,
                "transitive": transitive,
                "direct_count": len(direct),
                "transitive_count": len(transitive)
            }

        # Group by type
        affected_by_type = {}
        for artifact_id, data in all_affected.items():
            for node in data["transitive"]:
                atype = self.graph.graph.nodes[node].get("artifact_type", "unknown")
                affected_by_type.setdefault(atype, set()).add(node)

        # Risk assessment
        total = sum(len(nodes) for nodes in affected_by_type.values())
        if total > 10:
            risk = "🔴 High"
        elif total > 3:
            risk = "🟡 Medium"
        else:
            risk = "🟢 Low"

        if format == "json":
            return json.dumps({
                "artifacts_analyzed": artifact_ids,
                "impact": all_affected,
                "by_type": {k: list(v) for k, v in affected_by_type.items()},
                "total_affected": total,
                "risk": risk.split(" ")[1]
            }, indent=2)

        # Markdown
        lines = ["# Impact Report", ""]
        lines.append(f"**Risk Level:** {risk}")
        lines.append(f"**Total Affected:** {total} artifacts")
        lines.append("")

        for artifact_id, data in all_affected.items():
            lines.append(f"## {artifact_id}")
            lines.append(f"- Direct dependents: {data['direct_count']}")
            lines.append(f"- Transitive dependents: {data['transitive_count']}")
            lines.append("")

        if affected_by_type:
            lines.append("## Affected by Type")
            for atype, nodes in sorted(affected_by_type.items()):
                lines.append(f"### {atype}s ({len(nodes)})")
                for node in sorted(nodes):
                    lines.append(f"- {node}")
                lines.append("")

        return "\n".join(lines)

    def _transitive_downstream(self, artifact_id: str) -> list[str]:
        """Get all transitive downstream dependencies."""
        visited = set()
        queue = [artifact_id]

        while queue:
            current = queue.pop(0)
            for successor in self.graph.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    queue.append(successor)

        # Remove the starting artifact if it ended up in visited (due to cycles)
        visited.discard(artifact_id)
        return list(visited)

    # === REQ-DECISION-LOG-001: Decision Log ===

    def export_decision_log(self, since: Optional[str] = None, format: str = "md") -> str:
        """Chronological decision log."""
        decisions = []
        for node, data in self.graph.graph.nodes(data=True):
            if data.get("artifact_type") != "decision":
                continue

            decisions.append({
                "id": node,
                "file_path": data.get("file_path"),
                "state": data.get("state", "unknown"),
                "tags": data.get("tags", [])
            })

        # Sort by ID (which often has date prefix)
        decisions.sort(key=lambda x: x["id"])

        # Filter by date if provided
        if since:
            # Simple filter - assumes IDs or paths contain dates
            decisions = [d for d in decisions if since in d["id"] or since in str(d.get("file_path", ""))]

        if format == "json":
            return json.dumps(decisions, indent=2)

        # Markdown
        lines = ["# Decision Log", ""]

        for dec in decisions:
            lines.append(f"## {dec['id']}")
            if dec["file_path"]:
                lines.append(f"**File:** {dec['file_path']}")
            lines.append(f"**Status:** {dec['state']}")
            if dec["tags"]:
                lines.append(f"**Tags:** {', '.join(dec['tags'])}")
            lines.append("")

        return "\n".join(lines)
