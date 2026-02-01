#!/usr/bin/env python
"""Bootstrap scan: Register all repository artifacts with tags and relationships."""
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from mcp_server.server import TraceabilityServer


class BootstrapScanner:
    """Scan repository and register all artifacts."""

    def __init__(self, repo_root: str, trace_dir: str = ".trace"):
        self.repo_root = Path(repo_root)
        self.server = TraceabilityServer(trace_dir)

        # Track what we've done
        self.artifacts_added = 0
        self.artifacts_existing = 0
        self.links_proposed = 0

        # Skip patterns
        self.skip_dirs = {
            '.git', '.pytest_cache', '__pycache__', '.trace',
            'handoffs', 'cc_tasks', '.claude', 'venv', 'env'
        }
        self.skip_files = {'.DS_Store', '.gitignore', '.gitkeep'}
        self.skip_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.egg-info'}

    def artifact_exists(self, artifact_id: str) -> bool:
        """Check if artifact already exists in the graph."""
        return artifact_id in self.server.graph.graph

    def register_artifact(self, artifact_id: str, artifact_type: str,
                         file_path: str, tags: List[str]) -> bool:
        """Register an artifact if it doesn't already exist."""
        if self.artifact_exists(artifact_id):
            self.artifacts_existing += 1
            return False

        result = self.server._handle_add_artifact({
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "file_path": file_path,
            "tags": tags,
        })

        if result.get("success"):
            self.artifacts_added += 1
            return True
        return False

    def propose_link(self, source_id: str, target_id: str,
                    relationship_type: str, rationale: str) -> bool:
        """Propose a link if both artifacts exist."""
        if not self.artifact_exists(source_id) or not self.artifact_exists(target_id):
            return False

        # Check if link already exists
        if self.server.graph.graph.has_edge(source_id, target_id):
            return False

        result = self.server._handle_propose_link({
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "rationale": rationale,
        })

        if result.get("success"):
            self.links_proposed += 1
            return True
        return False

    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        # Skip directories
        if path.is_dir() and path.name in self.skip_dirs:
            return True

        # Skip files
        if path.name in self.skip_files:
            return True

        # Skip extensions
        if path.suffix in self.skip_extensions:
            return True

        # Skip if in a skip directory
        for parent in path.parents:
            if parent.name in self.skip_dirs:
                return True

        return False

    def infer_tags_from_path(self, file_path: Path) -> List[str]:
        """Infer tags from file path."""
        tags = []

        # Add directory-based tags
        parts = file_path.parts

        if 'docs' in parts:
            tags.append('doc')
        if 'tests' in parts:
            tags.append('test')
        if 'src' in parts:
            tags.append('core')
        if 'trace_core' in parts:
            tags.append('core')
        if 'mcp_server' in parts:
            tags.extend(['mcp', 'server'])
        if 'scripts' in parts:
            tags.append('automation')

        # Add specific tags based on filename
        name = file_path.stem.lower()

        if 'model' in name:
            tags.append('data-model')
        if 'query' in name or 'queries' in name:
            tags.append('query')
        if 'event' in name:
            tags.append('event-log')
        if 'graph' in name:
            tags.append('graph')
        if 'parser' in name:
            tags.append('parser')
        if 'config' in name or name == 'pyproject':
            tags.append('config')
        if 'readme' in name or name == 'claude':
            tags.extend(['meta', 'onboarding'])
        if 'roadmap' in name:
            tags.extend(['planning', 'future'])
        if 'design' in name or 'architecture' in name:
            tags.extend(['architecture', 'design'])
        if 'decision' in name:
            tags.append('decision')

        return list(set(tags))  # Remove duplicates

    def determine_artifact_type(self, file_path: Path) -> str:
        """Determine artifact type from file path and content."""
        name = file_path.name.lower()

        # Python files
        if file_path.suffix == '.py':
            if 'test' in file_path.parts or name.startswith('test_'):
                return 'test'
            return 'module'

        # Markdown files
        if file_path.suffix == '.md':
            if 'decision' in name:
                return 'decision'
            if 'requirement' in name or 'spec' in name:
                return 'requirement'
            return 'document'

        # Config files
        if name in ['pyproject.toml', 'setup.py', 'setup.cfg']:
            return 'document'

        return 'document'

    def parse_python_imports(self, file_path: Path) -> Set[str]:
        """Parse Python file to extract internal imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return set()

        imports = set()

        for node in ast.walk(tree):
            # Handle 'import x' and 'import x.y'
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in ['trace_core', 'mcp_server']:
                        imports.add(module)

            # Handle 'from x import y'
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in ['trace_core', 'mcp_server']:
                        imports.add(node.module)

        return imports

    def map_import_to_file(self, import_path: str) -> str | None:
        """Map Python import path to artifact ID (file path)."""
        # trace_core.models → src/trace_core/models.py
        # mcp_server.server → mcp_server/server.py

        parts = import_path.split('.')

        if parts[0] == 'trace_core':
            # src/trace_core/...
            file_path = self.repo_root / 'src' / '/'.join(parts)
            py_file = file_path.with_suffix('.py')
            if py_file.exists():
                return str(py_file.relative_to(self.repo_root))
            # Try __init__.py
            init_file = file_path / '__init__.py'
            if init_file.exists():
                return str(init_file.relative_to(self.repo_root))

        elif parts[0] == 'mcp_server':
            # mcp_server/...
            file_path = self.repo_root / '/'.join(parts)
            py_file = file_path.with_suffix('.py')
            if py_file.exists():
                return str(py_file.relative_to(self.repo_root))
            # Try __init__.py
            init_file = file_path / '__init__.py'
            if init_file.exists():
                return str(init_file.relative_to(self.repo_root))

        return None

    def match_test_to_source(self, test_file: Path) -> str | None:
        """Match test file to source file it tests."""
        # test_models.py → src/trace_core/models.py
        # test_mcp_server.py → mcp_server/server.py

        name = test_file.stem
        if name.startswith('test_'):
            source_name = name[5:]  # Remove 'test_' prefix

            # Try different locations
            candidates = [
                self.repo_root / 'src' / 'trace_core' / f'{source_name}.py',
                self.repo_root / 'mcp_server' / f'{source_name}.py',
            ]

            for candidate in candidates:
                if candidate.exists():
                    return str(candidate.relative_to(self.repo_root))

        return None

    def scan_and_register(self):
        """Main scan process."""
        print("=== Bootstrap Scan: Registering Repository Artifacts ===\n")

        # Phase 1: Register all files
        print("Phase 1: Scanning and registering files...")
        all_files = []

        for file_path in self.repo_root.rglob('*'):
            if file_path.is_file() and not self.should_skip(file_path):
                all_files.append(file_path)

        print(f"  Found {len(all_files)} files to process\n")

        # Register artifacts
        for file_path in sorted(all_files):
            rel_path = str(file_path.relative_to(self.repo_root))
            artifact_type = self.determine_artifact_type(file_path)
            tags = self.infer_tags_from_path(file_path)

            if self.register_artifact(rel_path, artifact_type, rel_path, tags):
                print(f"  ✓ {rel_path} ({artifact_type}, tags: {tags})")

        print(f"\n  Registered: {self.artifacts_added} new, {self.artifacts_existing} existing\n")

        # Phase 2: Infer relationships from Python imports
        print("Phase 2: Inferring dependencies from imports...")

        python_files = [f for f in all_files if f.suffix == '.py']

        for py_file in python_files:
            rel_path = str(py_file.relative_to(self.repo_root))
            imports = self.parse_python_imports(py_file)

            for import_path in imports:
                target_file = self.map_import_to_file(import_path)
                if target_file and target_file != rel_path:
                    if self.propose_link(
                        rel_path,
                        target_file,
                        "depends_on",
                        f"{rel_path} imports from {import_path}"
                    ):
                        print(f"  ✓ {rel_path} → {target_file} (depends_on)")

        print()

        # Phase 3: Match tests to source files
        print("Phase 3: Linking tests to source files...")

        test_files = [f for f in python_files if 'test' in f.parts or f.name.startswith('test_')]

        for test_file in test_files:
            test_path = str(test_file.relative_to(self.repo_root))
            source_file = self.match_test_to_source(test_file)

            if source_file:
                if self.propose_link(
                    test_path,
                    source_file,
                    "verifies",
                    f"{test_path} tests {source_file}"
                ):
                    print(f"  ✓ {test_path} → {source_file} (verifies)")

        print()

        # Summary
        print("=== Bootstrap Complete ===")
        print(f"Artifacts registered: {self.artifacts_added + self.artifacts_existing} "
              f"({self.artifacts_added} new, {self.artifacts_existing} existing)")
        print(f"Links proposed: {self.links_proposed}")
        print("\nRun proposed_links() to review pending approvals")
        print()


def main():
    """Run bootstrap scan."""
    import os
    repo_root = os.getcwd()

    scanner = BootstrapScanner(repo_root)
    scanner.scan_and_register()


if __name__ == "__main__":
    main()
