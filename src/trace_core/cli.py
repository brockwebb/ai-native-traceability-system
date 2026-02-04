"""CLI for trace system initialization."""
import sys
import click
from pathlib import Path


@click.group()
@click.version_option(version="0.3.0", prog_name="trace")
def cli():
    """AI-native traceability system.

    Initialize and manage traceability in your repositories.
    """
    pass


@cli.command()
@click.option('--template', '-t',
              type=click.Choice(['systems-engineering', 'agile', 'lightweight', 'auto']),
              default='auto',
              help='Methodology template (default: auto-detect)')
@click.option('--skip-scan', is_flag=True,
              help='Skip bootstrap scan')
@click.option('--skip-mcp', is_flag=True,
              help='Skip .mcp.json generation')
@click.option('--skip-skill', is_flag=True,
              help='Skip skill file installation')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without doing it')
@click.argument('path', default='.', type=click.Path(exists=True))
def init(template, skip_scan, skip_mcp, skip_skill, dry_run, path):
    """Initialize traceability in a repository.

    PATH defaults to current directory.

    Examples:

        \b
        # Initialize in current directory (auto-detect template)
        trace init

        \b
        # Initialize with specific template
        trace init --template systems-engineering

        \b
        # Dry run to see what would happen
        trace init --dry-run

        \b
        # Initialize another project
        trace init ~/projects/my-other-repo
    """
    from .init import TraceInitializer

    initializer = TraceInitializer(Path(path).resolve())
    result = initializer.run(
        template=template,
        skip_scan=skip_scan,
        skip_mcp=skip_mcp,
        skip_skill=skip_skill,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo("\n[Dry run - no changes made]")

    sys.exit(0 if result.success else 1)


@cli.command()
@click.argument('path', default='.', type=click.Path(exists=True))
def status(path):
    """Check traceability status of a repository.

    Examples:

        \b
        # Check current directory
        trace status

        \b
        # Check another directory
        trace status ~/projects/my-repo
    """
    from .events import EventLog

    repo = Path(path).resolve()
    trace_dir = repo / ".trace"

    if not trace_dir.exists():
        click.echo(f"❌ Not initialized")
        click.echo(f"\nRun: trace init {path if path != '.' else ''}")
        sys.exit(1)

    events_file = trace_dir / "events.jsonl"

    # Count events
    event_count = 0
    if events_file.exists():
        try:
            with open(events_file) as f:
                event_count = sum(1 for _ in f)
        except:
            pass

    # Count artifacts (ARTIFACT_ADDED events)
    artifact_count = 0
    if events_file.exists():
        try:
            event_log = EventLog(str(trace_dir))
            event_log.init()
            from .graph import TraceGraph
            graph = TraceGraph(event_log)
            graph.rebuild()
            artifact_count = len(list(graph.graph.nodes()))
        except:
            pass

    click.echo(f"✓ Traceability initialized")
    click.echo(f"\n  Directory: {trace_dir}")
    click.echo(f"  Events: {event_count}")
    click.echo(f"  Artifacts: {artifact_count}")

    # Check for MCP config
    mcp_path = repo / ".mcp.json"
    if mcp_path.exists():
        click.echo(f"  MCP config: ✓")
    else:
        click.echo(f"  MCP config: ✗ (run 'trace init' to create)")

    # Check for skill file
    skill_path = repo / ".claude" / "skills" / "traceability.md"
    if skill_path.exists():
        click.echo(f"  Skill file: ✓")
    elif (repo / ".claude").exists():
        click.echo(f"  Skill file: ✗ (run 'trace init' to install)")


if __name__ == "__main__":
    cli()
