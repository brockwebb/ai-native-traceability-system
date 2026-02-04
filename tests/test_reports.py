"""Tests for report generation functionality."""
import pytest

from trace_core import ReportGenerator


class TestExportMermaid:
    """Tests for Mermaid diagram export (REQ-EXPORT-MERMAID-001)."""

    def test_export_all_artifacts(self, graph_with_data):
        """Test exporting all artifacts as Mermaid diagram."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_mermaid()

        assert "flowchart TD" in result
        assert "subgraph" in result
        # Check for artifact nodes
        assert "REQ-001" in result or "REQ_001" in result
        assert "auth.py" in result or "auth_py" in result

    def test_export_with_root_node(self, graph_with_data):
        """Test exporting subgraph from root node."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_mermaid(root="auth.py", depth=1)

        assert "flowchart TD" in result
        # Should include auth.py and its neighbors
        assert "auth" in result.lower()

    def test_export_with_direction_downstream(self, graph_with_data):
        """Test exporting only downstream dependencies."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_mermaid(root="auth.py", direction="downstream")

        assert "flowchart TD" in result
        # Should include downstream from auth.py (REQ-001)
        assert "REQ" in result

    def test_export_with_artifact_type_filter(self, graph_with_data):
        """Test filtering by artifact type."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_mermaid(artifact_types=["requirement"])

        assert "flowchart TD" in result
        assert "REQ" in result
        # Modules should not appear
        assert "auth_py" not in result or "subgraph modules" not in result

    def test_export_with_relationship_filter(self, graph_with_data):
        """Test filtering by relationship type."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_mermaid(relationship_types=["implements"])

        assert "flowchart TD" in result
        # Should show implements relationships
        if "implements" in result:
            assert "-->" in result

    def test_mermaid_safe_id_conversion(self, graph_with_data):
        """Test that special characters are converted to safe IDs."""
        generator = ReportGenerator(graph_with_data)
        safe_id = generator._mermaid_safe_id("src/auth.py")

        assert "/" not in safe_id
        assert "." not in safe_id
        assert "_" in safe_id


class TestExportDependencyMap:
    """Tests for dependency map export (REQ-DEP-001)."""

    def test_export_mermaid_format(self, graph_with_data):
        """Test exporting dependency map as Mermaid."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_dependency_map(format="mermaid")

        assert "flowchart TD" in result

    def test_export_dot_format(self, graph_with_data):
        """Test exporting dependency map as DOT."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_dependency_map(format="dot")

        assert "digraph G" in result
        assert "rankdir=TB" in result
        assert "->" in result

    def test_export_json_format(self, graph_with_data):
        """Test exporting dependency map as JSON."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_dependency_map(format="json")

        import json
        data = json.loads(result)
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0
        # Check node structure
        assert "id" in data["nodes"][0]
        assert "artifact_type" in data["nodes"][0]
        # Check edge structure
        assert "source" in data["edges"][0]
        assert "target" in data["edges"][0]
        assert "relationship_type" in data["edges"][0]

    def test_export_with_filters(self, graph_with_data):
        """Test exporting with artifact and relationship filters."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_dependency_map(
            format="json",
            artifact_types=["module"],
            relationship_types=["depends_on"]
        )

        import json
        data = json.loads(result)
        # All nodes should be modules
        for node in data["nodes"]:
            assert node["artifact_type"] == "module"
        # All edges should be depends_on
        for edge in data["edges"]:
            assert edge["relationship_type"] == "depends_on"

    def test_invalid_format_raises_error(self, graph_with_data):
        """Test that invalid format raises ValueError."""
        generator = ReportGenerator(graph_with_data)
        with pytest.raises(ValueError, match="Unknown format"):
            generator.export_dependency_map(format="invalid")


class TestExportCoverageReport:
    """Tests for coverage report (REQ-COV-001)."""

    def test_coverage_report_markdown(self, graph_with_orphans):
        """Test generating coverage report in markdown format."""
        generator = ReportGenerator(graph_with_orphans)
        result = generator.export_coverage_report(format="md")

        assert "# Coverage Report" in result
        assert "## Summary" in result
        assert "orphan" in result.lower()
        assert "untested" in result.lower()

    def test_coverage_report_json(self, graph_with_orphans):
        """Test generating coverage report in JSON format."""
        generator = ReportGenerator(graph_with_orphans)
        result = generator.export_coverage_report(format="json")

        import json
        data = json.loads(result)
        assert "orphan_requirements" in data
        assert "untested_modules" in data
        assert "undocumented_decisions" in data
        assert "summary" in data
        # Should find the orphan requirement
        assert "REQ-ORPHAN" in data["orphan_requirements"]
        # Should find the untested module
        assert "untested.py" in data["untested_modules"]

    def test_coverage_with_complete_traceability(self, graph_with_data):
        """Test coverage report shows good traceability."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_coverage_report(format="json")

        import json
        data = json.loads(result)
        # Should have some orphans (REQ-002)
        assert len(data["orphan_requirements"]) >= 1
        # Should have some untested (api.py)
        assert len(data["untested_modules"]) >= 1

    def test_pending_approvals_count(self, event_log):
        """Test counting pending approvals."""
        from trace_core import Event, TraceGraph
        from trace_core.models import EventType, State

        # Add artifacts
        event_log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "A", "artifact_type": "module"},
        ))
        event_log.append(Event(
            event_type=EventType.ARTIFACT_ADDED,
            payload={"artifact_id": "B", "artifact_type": "requirement"},
        ))

        # Add proposed link
        event_log.append(Event(
            event_type=EventType.LINK_ADDED,
            payload={
                "source_id": "A",
                "target_id": "B",
                "relationship_type": "implements",
            },
            state=State.PROPOSED,
        ))

        graph = TraceGraph(event_log)
        graph.rebuild()
        generator = ReportGenerator(graph)
        result = generator.export_coverage_report(format="json")

        import json
        data = json.loads(result)
        assert data["pending_approvals"] == 1


class TestExportRTM:
    """Tests for Requirements Traceability Matrix (REQ-RTM-001)."""

    def test_rtm_markdown_format(self, graph_with_data):
        """Test generating RTM in markdown format."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_rtm(format="md")

        assert "# Requirements Traceability Matrix" in result
        assert "| Requirement | Implementations | Tests | Status |" in result
        assert "REQ-001" in result
        assert "REQ-002" in result

    def test_rtm_csv_format(self, graph_with_data):
        """Test generating RTM in CSV format."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_rtm(format="csv")

        assert "Requirement,Implementations,Tests,Status" in result
        assert "REQ-001" in result
        # CSV should not have emoji
        assert "✅" not in result

    def test_rtm_json_format(self, graph_with_data):
        """Test generating RTM in JSON format."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_rtm(format="json")

        import json
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) >= 2  # REQ-001 and REQ-002
        # Check structure
        req = data[0]
        assert "requirement" in req
        assert "implementations" in req
        assert "tests" in req
        assert "status" in req

    def test_rtm_status_fully_traced(self, graph_with_data):
        """Test RTM shows fully traced requirement."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_rtm(format="json")

        import json
        data = json.loads(result)
        # Find REQ-001
        req_001 = next((r for r in data if r["requirement"] == "REQ-001"), None)
        assert req_001 is not None
        assert len(req_001["implementations"]) > 0  # has auth.py
        assert len(req_001["tests"]) > 0  # has test_auth.py (via auth.py)
        assert "Fully Traced" in req_001["status"]

    def test_rtm_status_orphan(self, graph_with_orphans):
        """Test RTM shows orphan requirement."""
        generator = ReportGenerator(graph_with_orphans)
        result = generator.export_rtm(format="json")

        import json
        data = json.loads(result)
        # Find orphan requirement
        orphan = next((r for r in data if r["requirement"] == "REQ-ORPHAN"), None)
        assert orphan is not None
        assert len(orphan["implementations"]) == 0
        assert len(orphan["tests"]) == 0
        assert "Orphan" in orphan["status"]


class TestExportImpactReport:
    """Tests for impact analysis report (REQ-IMPACT-RPT-001)."""

    def test_impact_report_markdown(self, large_graph):
        """Test generating impact report in markdown format."""
        generator = ReportGenerator(large_graph)
        result = generator.export_impact_report(artifact_ids=["A"], format="md")

        assert "# Impact Report" in result
        assert "Risk Level" in result
        assert "Total Affected" in result
        assert "## A" in result
        assert "Direct dependents" in result
        assert "Transitive dependents" in result

    def test_impact_report_json(self, large_graph):
        """Test generating impact report in JSON format."""
        generator = ReportGenerator(large_graph)
        result = generator.export_impact_report(artifact_ids=["A"], format="json")

        import json
        data = json.loads(result)
        assert "artifacts_analyzed" in data
        assert "impact" in data
        assert "by_type" in data
        assert "total_affected" in data
        assert "risk" in data

    def test_impact_transitive_dependencies(self, large_graph):
        """Test that impact analysis finds transitive dependencies."""
        generator = ReportGenerator(large_graph)
        result = generator.export_impact_report(artifact_ids=["A"], format="json")

        import json
        data = json.loads(result)
        # A -> B -> C -> D, so changing A affects B, C, D (3 artifacts)
        assert data["impact"]["A"]["transitive_count"] == 3
        assert "B" in data["impact"]["A"]["transitive"]
        assert "C" in data["impact"]["A"]["transitive"]
        assert "D" in data["impact"]["A"]["transitive"]

    def test_impact_direct_dependencies_only(self, large_graph):
        """Test direct dependencies vs transitive."""
        generator = ReportGenerator(large_graph)
        result = generator.export_impact_report(artifact_ids=["A"], format="json")

        import json
        data = json.loads(result)
        # A -> B directly
        assert data["impact"]["A"]["direct_count"] == 1
        assert "B" in data["impact"]["A"]["direct"]

    def test_impact_risk_assessment_high(self, large_graph):
        """Test high risk assessment for many affected artifacts."""
        generator = ReportGenerator(large_graph)
        # Add more artifacts to trigger high risk (>10 affected)
        for i in range(15):
            from trace_core.models import EventType, State
            generator.graph.graph.add_node(f"X{i}", artifact_type="module")
            generator.graph.graph.add_edge("A", f"X{i}", relationship_type="depends_on", state=State.AUTHORITATIVE.value)

        result = generator.export_impact_report(artifact_ids=["A"], format="json")

        import json
        data = json.loads(result)
        # More than 10 affected should be High risk
        assert data["total_affected"] > 10
        assert data["risk"] == "High"

    def test_impact_risk_assessment_medium(self, graph_with_data):
        """Test medium risk assessment."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_impact_report(artifact_ids=["auth.py"], format="json")

        import json
        data = json.loads(result)
        # Medium risk is 3-10 affected
        if 3 < data["total_affected"] <= 10:
            assert data["risk"] == "Medium"

    def test_impact_multiple_artifacts(self, large_graph):
        """Test impact analysis for multiple artifacts."""
        generator = ReportGenerator(large_graph)
        result = generator.export_impact_report(artifact_ids=["A", "B"], format="json")

        import json
        data = json.loads(result)
        assert "A" in data["impact"]
        assert "B" in data["impact"]
        assert data["artifacts_analyzed"] == ["A", "B"]

    def test_impact_nonexistent_artifact(self, graph_with_data):
        """Test impact analysis handles nonexistent artifact gracefully."""
        generator = ReportGenerator(graph_with_data)
        result = generator.export_impact_report(artifact_ids=["NONEXISTENT"], format="json")

        import json
        data = json.loads(result)
        # Should return empty impact for nonexistent artifact
        assert data["total_affected"] == 0


class TestExportDecisionLog:
    """Tests for decision log export (REQ-DECISION-LOG-001)."""

    def test_decision_log_markdown(self, graph_with_decisions):
        """Test generating decision log in markdown format."""
        generator = ReportGenerator(graph_with_decisions)
        result = generator.export_decision_log(format="md")

        assert "# Decision Log" in result
        assert "DEC-001-database-choice" in result
        assert "DEC-002-api-framework" in result
        assert "**File:**" in result
        assert "**Status:**" in result

    def test_decision_log_json(self, graph_with_decisions):
        """Test generating decision log in JSON format."""
        generator = ReportGenerator(graph_with_decisions)
        result = generator.export_decision_log(format="json")

        import json
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 3  # DEC-001, DEC-002, DEC-003
        # Check structure
        dec = data[0]
        assert "id" in dec
        assert "file_path" in dec
        assert "state" in dec
        assert "tags" in dec

    def test_decision_log_chronological_order(self, graph_with_decisions):
        """Test that decisions are sorted chronologically by ID."""
        generator = ReportGenerator(graph_with_decisions)
        result = generator.export_decision_log(format="json")

        import json
        data = json.loads(result)
        ids = [d["id"] for d in data]
        # Should be sorted
        assert ids == sorted(ids)

    def test_decision_log_with_date_filter(self, graph_with_decisions):
        """Test filtering decisions by date string."""
        generator = ReportGenerator(graph_with_decisions)
        result = generator.export_decision_log(since="001", format="json")

        import json
        data = json.loads(result)
        # Should only include decisions with "001" in ID or path
        for dec in data:
            assert "001" in dec["id"] or ("file_path" in dec and dec["file_path"] and "001" in dec["file_path"])

    def test_decision_log_with_tags(self, graph_with_decisions):
        """Test that decision log includes tags."""
        generator = ReportGenerator(graph_with_decisions)
        result = generator.export_decision_log(format="json")

        import json
        data = json.loads(result)
        # Find decision with tags
        dec_001 = next((d for d in data if d["id"] == "DEC-001-database-choice"), None)
        assert dec_001 is not None
        assert "architecture" in dec_001["tags"]

    def test_decision_log_empty_graph(self, empty_graph):
        """Test decision log with no decisions."""
        generator = ReportGenerator(empty_graph)
        result = generator.export_decision_log(format="json")

        import json
        data = json.loads(result)
        assert data == []


class TestGetSubgraph:
    """Tests for subgraph traversal helper."""

    def test_get_subgraph_with_depth(self, large_graph):
        """Test getting subgraph with depth limit."""
        generator = ReportGenerator(large_graph)
        nodes = generator._get_subgraph("A", depth=1, direction="downstream")

        assert "A" in nodes
        assert "B" in nodes
        # Should not include C (depth 2)
        assert "C" not in nodes

    def test_get_subgraph_upstream(self, large_graph):
        """Test getting upstream subgraph."""
        generator = ReportGenerator(large_graph)
        nodes = generator._get_subgraph("D", depth=2, direction="upstream")

        assert "D" in nodes
        assert "C" in nodes
        assert "B" in nodes
        # A is 3 hops away
        assert "A" not in nodes

    def test_get_subgraph_both_directions(self, graph_with_data):
        """Test getting subgraph in both directions."""
        generator = ReportGenerator(graph_with_data)
        nodes = generator._get_subgraph("auth.py", depth=1, direction="both")

        assert "auth.py" in nodes
        # Should include neighbors in both directions
        assert len(nodes) > 1


class TestTransitiveDownstream:
    """Tests for transitive downstream helper."""

    def test_transitive_downstream_chain(self, large_graph):
        """Test finding all transitive downstream dependencies."""
        generator = ReportGenerator(large_graph)
        downstream = generator._transitive_downstream("A")

        assert "B" in downstream
        assert "C" in downstream
        assert "D" in downstream
        assert "A" not in downstream  # Should not include self

    def test_transitive_downstream_no_dependencies(self, large_graph):
        """Test artifact with no downstream dependencies."""
        generator = ReportGenerator(large_graph)
        downstream = generator._transitive_downstream("D")

        assert downstream == []

    def test_transitive_downstream_cycles(self, event_log):
        """Test handling of cycles in dependency graph."""
        from trace_core import Event, TraceGraph
        from trace_core.models import EventType, State

        # Create cycle: A -> B -> C -> A
        for name in ["A", "B", "C"]:
            event_log.append(Event(
                event_type=EventType.ARTIFACT_ADDED,
                payload={"artifact_id": name, "artifact_type": "module"},
            ))

        for source, target in [("A", "B"), ("B", "C"), ("C", "A")]:
            event_log.append(Event(
                event_type=EventType.LINK_ADDED,
                payload={
                    "source_id": source,
                    "target_id": target,
                    "relationship_type": "depends_on",
                },
                state=State.AUTHORITATIVE,
            ))

        graph = TraceGraph(event_log)
        graph.rebuild()
        generator = ReportGenerator(graph)

        # Should handle cycle without infinite loop
        downstream = generator._transitive_downstream("A")
        assert set(downstream) == {"B", "C"}
