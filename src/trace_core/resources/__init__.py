"""Package resources for trace initialization."""
from importlib import resources
from pathlib import Path


def get_template(name: str) -> str:
    """Get template content by name.

    Args:
        name: Template name without .yaml extension (e.g., 'systems-engineering')

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    try:
        # Python 3.9+ way
        return resources.files(__package__).joinpath(f"templates/{name}.yaml").read_text()
    except AttributeError:
        # Fallback for Python 3.7-3.8
        import pkg_resources
        return pkg_resources.resource_string(__package__, f"templates/{name}.yaml").decode('utf-8')


def get_skill_file() -> str:
    """Get skill file content.

    Returns:
        Skill file content as string
    """
    try:
        return resources.files(__package__).joinpath("skill_file.md").read_text()
    except AttributeError:
        import pkg_resources
        return pkg_resources.resource_string(__package__, "skill_file.md").decode('utf-8')


def list_templates() -> list[str]:
    """List available template names.

    Returns:
        List of template names without .yaml extension
    """
    try:
        templates_dir = resources.files(__package__).joinpath("templates")
        return sorted([f.stem for f in templates_dir.iterdir() if f.suffix == ".yaml"])
    except AttributeError:
        import pkg_resources
        templates = pkg_resources.resource_listdir(__package__, "templates")
        return sorted([f[:-5] for f in templates if f.endswith(".yaml")])
