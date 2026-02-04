"""Markdown parser for extracting heading anchors."""
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Anchor:
    """A location anchor within a file."""
    anchor_id: str
    file_path: str
    heading: str
    level: int
    line_start: int
    line_end: int | None
    content_hash: str


class MarkdownParser:
    """Extract heading anchors from Markdown files."""

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")

    def parse_links(self, file_path: Path | str) -> set[str]:
        """Parse Markdown file to extract internal file links.

        Args:
            file_path: Path to Markdown file

        Returns:
            Set of relative file paths linked in the document
            (excludes http/https URLs, anchor-only links)
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return set()

        content = file_path.read_text()
        links = set()

        for match in self.LINK_PATTERN.finditer(content):
            link_target = match.group(2).strip()

            # Skip external URLs
            if link_target.startswith(('http://', 'https://', 'mailto:')):
                continue

            # Skip anchor-only links
            if link_target.startswith('#'):
                continue

            # Remove fragment identifier if present
            if '#' in link_target:
                link_target = link_target.split('#')[0]

            if link_target:
                links.add(link_target)

        return links

    def parse(self, file_path: Path | str) -> list[Anchor]:
        """Parse markdown file and extract heading anchors."""
        file_path = Path(file_path)
        if not file_path.exists():
            return []

        lines = file_path.read_text().splitlines()
        anchors = []
        heading_stack: list[tuple[int, int, str]] = []  # (level, line_num, heading)

        for i, line in enumerate(lines, start=1):
            match = self.HEADING_PATTERN.match(line)
            if match:
                level = len(match.group(1))
                heading = match.group(2).strip()

                # Close previous headings at same or higher level
                while heading_stack and heading_stack[-1][0] >= level:
                    prev_level, prev_line, prev_heading = heading_stack.pop()
                    content = "\n".join(lines[prev_line - 1 : i - 1])
                    anchors.append(self._make_anchor(
                        file_path, prev_heading, prev_level, prev_line, i - 1, content
                    ))

                heading_stack.append((level, i, heading))

        # Close remaining headings
        for level, line_num, heading in heading_stack:
            content = "\n".join(lines[line_num - 1 :])
            anchors.append(self._make_anchor(
                file_path, heading, level, line_num, len(lines), content
            ))

        return anchors

    def _make_anchor(
        self, file_path: Path, heading: str, level: int,
        line_start: int, line_end: int, content: str
    ) -> Anchor:
        """Create an anchor with content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        anchor_id = f"{file_path.stem}:{heading.lower().replace(' ', '-')}"
        return Anchor(
            anchor_id=anchor_id,
            file_path=str(file_path),
            heading=heading,
            level=level,
            line_start=line_start,
            line_end=line_end,
            content_hash=content_hash,
        )
