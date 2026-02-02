"""Template loading and artifact classification."""
from pathlib import Path
from typing import Optional
import yaml


class TemplateLoader:
    """Load and query methodology templates."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self._cache: dict = {}

    def list_templates(self) -> list[str]:
        """Return available template names."""
        if not self.templates_dir.exists():
            return []
        return [p.stem for p in self.templates_dir.glob("*.yaml")]

    def get_template(self, name: str) -> Optional[dict]:
        """Load template by name."""
        if name in self._cache:
            return self._cache[name]

        path = self.templates_dir / f"{name}.yaml"
        if not path.exists():
            return None

        with open(path) as f:
            template = yaml.safe_load(f)

        self._cache[name] = template
        return template

    def classify_file(self, file_path: str, template_name: Optional[str] = None) -> Optional[str]:
        """Suggest artifact type for file based on template patterns.

        If template_name is None, tries all templates and returns first match.
        Returns artifact_type id or None.
        """
        templates = [template_name] if template_name else self.list_templates()
        path = Path(file_path)

        for tname in templates:
            template = self.get_template(tname)
            if not template:
                continue

            for atype in template.get("artifact_types", []):
                for pattern in atype.get("file_patterns", []):
                    # Use Path.match() which supports ** glob patterns
                    if path.match(pattern):
                        return atype["id"]

                    # Also try without **/ prefix for root-level files
                    # (Path("README.md").match("**/*.md") returns False, but should match)
                    if pattern.startswith("**/") and path.match(pattern[3:]):
                        return atype["id"]

        return None

    def get_expected_relationships(self, template_name: str) -> list[dict]:
        """Return relationship chains for scaffolding."""
        template = self.get_template(template_name)
        if not template:
            return []
        return template.get("relationship_chains", [])
