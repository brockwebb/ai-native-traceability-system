"""Trace initialization logic."""
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import resources


@dataclass
class InitResult:
    """Result of trace initialization."""
    success: bool
    template_used: str
    artifacts_found: int = 0
    messages: list[str] = field(default_factory=list)


class TraceInitializer:
    """Initialize traceability in a repository."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.trace_dir = repo_root / ".trace"
        self.messages = []

    def log(self, msg: str):
        """Log a message."""
        print(f"  {msg}")
        self.messages.append(msg)

    def detect_project_type(self) -> str:
        """Auto-detect project type and return recommended template.

        Returns:
            'systems-engineering', 'agile', or 'lightweight'
        """
        # Systems Engineering signals
        se_signals = [
            self.repo_root / "docs" / "requirements",
            self.repo_root / "docs" / "architecture",
            self.repo_root / "docs" / "decisions",
        ]
        if any(p.exists() for p in se_signals):
            return "systems-engineering"

        # Check for multiple requirements files
        req_files = list(self.repo_root.glob("**/*requirements*.md"))
        if len(req_files) >= 2:
            return "systems-engineering"

        # Agile signals (tests + src structure)
        has_tests = (self.repo_root / "tests").exists()
        has_src = (self.repo_root / "src").exists()
        if has_tests and has_src:
            return "agile"

        # Default to lightweight
        return "lightweight"

    def is_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        return (self.repo_root / ".git").exists()

    def create_trace_dir(self, dry_run: bool = False) -> bool:
        """Create .trace/ directory structure."""
        if self.trace_dir.exists():
            self.log("✓ .trace/ already exists")
            return True

        if dry_run:
            self.log("Would create .trace/")
            return True

        self.trace_dir.mkdir()
        (self.trace_dir / "templates").mkdir()
        (self.trace_dir / "events.jsonl").touch()

        # Create README
        readme = self.trace_dir / "README.md"
        readme.write_text(
            "# Trace Data\n\n"
            "This directory contains traceability data for this repository.\n\n"
            "- `events.jsonl` - Event log (append-only)\n"
            "- `templates/` - Methodology templates\n\n"
            "Do not edit these files manually. Use trace tools.\n"
        )

        self.log("✓ Created .trace/")
        return True

    def install_templates(self, dry_run: bool = False) -> bool:
        """Copy templates to .trace/templates/."""
        templates_dir = self.trace_dir / "templates"

        for name in resources.list_templates():
            dest = templates_dir / f"{name}.yaml"
            if dest.exists():
                continue

            if dry_run:
                self.log(f"Would install template: {name}")
                continue

            content = resources.get_template(name)
            dest.write_text(content)
            self.log(f"✓ Installed template: {name}")

        return True

    def generate_mcp_json(self, dry_run: bool = False) -> bool:
        """Generate .mcp.json for Claude Desktop integration."""
        mcp_path = self.repo_root / ".mcp.json"

        if mcp_path.exists():
            self.log("✓ .mcp.json already exists")
            return True

        config = {
            "mcpServers": {
                "trace": {
                    "command": sys.executable,
                    "args": ["-m", "mcp_server.server"],
                    "cwd": str(self.repo_root),
                    "env": {
                        "TRACE_DIR": str(self.trace_dir)
                    }
                }
            }
        }

        if dry_run:
            self.log("Would create .mcp.json")
            return True

        mcp_path.write_text(json.dumps(config, indent=2) + "\n")
        self.log("✓ Created .mcp.json")
        return True

    def install_skill_file(self, dry_run: bool = False) -> bool:
        """Install CC skill file if .claude/ exists."""
        claude_dir = self.repo_root / ".claude"

        if not claude_dir.exists():
            self.log("⊘ No .claude/ directory - skipping skill file")
            return True

        skills_dir = claude_dir / "skills"
        skill_path = skills_dir / "traceability.md"

        if skill_path.exists():
            self.log("✓ Skill file already exists")
            return True

        if dry_run:
            self.log("Would install skill file")
            return True

        skills_dir.mkdir(exist_ok=True)
        content = resources.get_skill_file()
        skill_path.write_text(content)
        self.log("✓ Installed skill file")
        return True

    def run_bootstrap(self, dry_run: bool = False) -> int:
        """Run bootstrap scan to register existing artifacts.

        Returns:
            Number of artifacts found
        """
        if dry_run:
            self.log("Would run bootstrap scan")
            return 0

        # Import here to avoid circular deps
        from scripts.bootstrap_scan import BootstrapScanner

        scanner = BootstrapScanner(str(self.repo_root), str(self.trace_dir))
        scanner.scan_and_register()

        return scanner.artifacts_added + scanner.artifacts_existing

    def run(
        self,
        template: str = "auto",
        skip_scan: bool = False,
        skip_mcp: bool = False,
        skip_skill: bool = False,
        dry_run: bool = False,
    ) -> InitResult:
        """Run full initialization.

        Args:
            template: Template to use ('auto', 'systems-engineering', 'agile', 'lightweight')
            skip_scan: Skip bootstrap scan
            skip_mcp: Skip .mcp.json generation
            skip_skill: Skip skill file installation
            dry_run: Show what would be done without doing it

        Returns:
            InitResult with success status and metadata
        """
        print(f"\nInitializing traceability in: {self.repo_root}\n")

        # Check git repo
        if not self.is_git_repo():
            self.log("⚠ Warning: Not a git repository")

        # Detect or use specified template
        if template == "auto":
            template = self.detect_project_type()
            self.log(f"✓ Auto-detected project type: {template}")
        else:
            self.log(f"✓ Using template: {template}")

        # Create structure
        self.create_trace_dir(dry_run)
        self.install_templates(dry_run)

        # Optional: MCP config
        if not skip_mcp:
            self.generate_mcp_json(dry_run)

        # Optional: Skill file
        if not skip_skill:
            self.install_skill_file(dry_run)

        # Optional: Bootstrap scan
        artifacts_found = 0
        if not skip_scan and not dry_run:
            print("\nRunning bootstrap scan...\n")
            artifacts_found = self.run_bootstrap(dry_run)
        elif skip_scan:
            self.log("⊘ Skipping bootstrap scan")

        print("\n✓ Initialization complete!")
        print(f"  Template: {template}")
        if artifacts_found:
            print(f"  Artifacts: {artifacts_found}")
        print(f"\n  MCP server: trace-mcp")
        print(f"  Next: Restart Claude Desktop to load MCP server\n")

        return InitResult(
            success=True,
            template_used=template,
            artifacts_found=artifacts_found,
            messages=self.messages,
        )
