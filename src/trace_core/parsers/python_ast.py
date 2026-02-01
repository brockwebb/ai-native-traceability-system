"""Python AST parser for extracting function/class anchors."""
import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PythonAnchor:
    """A location anchor for Python code elements."""
    anchor_id: str
    file_path: str
    name: str
    anchor_type: str  # "function" | "class" | "method"
    line_start: int
    line_end: int
    content_hash: str


class PythonParser:
    """Extract function and class anchors from Python files."""

    def parse(self, file_path: Path | str) -> list[PythonAnchor]:
        """Parse Python file and extract function/class anchors."""
        file_path = Path(file_path)
        if not file_path.exists():
            return []

        source = file_path.read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        lines = source.splitlines()
        anchors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                anchors.append(self._make_anchor(
                    file_path, node.name, "function", node, lines
                ))
            elif isinstance(node, ast.AsyncFunctionDef):
                anchors.append(self._make_anchor(
                    file_path, node.name, "function", node, lines
                ))
            elif isinstance(node, ast.ClassDef):
                anchors.append(self._make_anchor(
                    file_path, node.name, "class", node, lines
                ))

        return anchors

    def _make_anchor(
        self, file_path: Path, name: str, anchor_type: str,
        node: ast.AST, lines: list[str]
    ) -> PythonAnchor:
        """Create an anchor with content hash."""
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        content = "\n".join(lines[line_start - 1 : line_end])
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        anchor_id = f"{file_path.stem}:{name}"

        return PythonAnchor(
            anchor_id=anchor_id,
            file_path=str(file_path),
            name=name,
            anchor_type=anchor_type,
            line_start=line_start,
            line_end=line_end,
            content_hash=content_hash,
        )
