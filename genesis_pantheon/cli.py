"""CLI entry point for GenesisPantheon."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from genesis_pantheon.blueprint import Blueprint
from genesis_pantheon.collective import Collective
from genesis_pantheon.constants import DEFAULT_CONFIG_FILE
from genesis_pantheon.nexus import Nexus

console = Console()

app = typer.Typer(
    name="genesispan",
    help=(
        "GenesisPantheon: Multi-agent AI framework for software development"
    ),
    add_completion=True,
    pretty_exceptions_show_locals=False,
)


@app.command()
def launch(
    mission: str = typer.Argument(
        ..., help="Project description / user requirement"
    ),
    budget: float = typer.Option(
        10.0, "--budget", "-b", help="Maximum budget in USD"
    ),
    n_rounds: int = typer.Option(
        5, "--rounds", "-r", help="Maximum execution rounds"
    ),
    code_review: int = typer.Option(
        1, "--code-review", help="Enable code review (1=yes, 0=no)"
    ),
    run_tests: int = typer.Option(
        0, "--run-tests", help="Run tests after generation (1=yes, 0=no)"
    ),
    project_name: str = typer.Option(
        "", "--name", "-n", help="Project name"
    ),
    project_path: str = typer.Option(
        "", "--output", "-o", help="Output directory path"
    ),
    config_file: str | None = typer.Option(
        None, "--config", "-c", help="Path to blueprint.yaml config"
    ),
) -> None:
    """Launch GenesisPantheon to build a software project.

    Example:

        genesispan launch "Build a 2048 game in Python"
    """
    from genesis_pantheon.personas import (
        CodeCrafter,
        MissionCoordinator,
        SystemArchitect,
        VisionDirector,
    )

    console.print(
        Panel(
            f"[bold green]GenesisPantheon[/bold green]\n"
            f"Mission: {mission[:100]}",
            title="Launching Collective",
        )
    )

    # Load configuration
    if config_file:
        bp = Blueprint.read(Path(config_file))
    else:
        bp = Blueprint.from_home()

    if project_name:
        bp.workspace.project_name = project_name
    if project_path:
        from pathlib import Path as _Path
        bp.workspace.path = _Path(project_path)

    ctx = Nexus()
    ctx.config = bp
    ctx.budget.max_budget = budget

    collective = Collective(context=ctx)
    collective.allocate_budget(budget)

    personas = [
        VisionDirector(),
        SystemArchitect(),
        CodeCrafter(code_review=bool(code_review > 0)),
        MissionCoordinator(),
    ]
    if run_tests > 0:
        from genesis_pantheon.personas import QualityGuardian
        personas.append(QualityGuardian())

    collective.recruit(personas)

    async def _run() -> None:
        signals = await collective.run(
            n_rounds=n_rounds,
            mission=mission,
        )
        ledger = collective.budget_ledger
        console.print(
            Panel(
                f"[green]Run complete![/green]\n"
                f"Signals: {len(signals)}\n"
                f"{ledger.summary()}",
                title="Finished",
            )
        )

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)


@app.command(name="init-config")
def init_config() -> None:
    """Create a default blueprint.yaml config file.

    The file is placed at ~/.genesis_pantheon/blueprint.yaml.
    """
    dest = DEFAULT_CONFIG_FILE
    if dest.exists():
        console.print(
            f"[yellow]Config already exists at {dest}[/yellow]"
        )
        overwrite = typer.confirm("Overwrite?", default=False)
        if not overwrite:
            raise typer.Exit()

    bp = Blueprint()
    bp.save(dest)
    console.print(
        f"[green]Config created at:[/green] {dest}\n"
        "Edit it to add your API keys and preferences."
    )


@app.command(name="list-oracles")
def list_oracles() -> None:
    """List all available oracle (LLM) providers."""
    from genesis_pantheon.configs.oracle_config import OracleApiType

    table = Table(title="Available Oracle Providers")
    table.add_column("Type", style="cyan")
    table.add_column("Description")
    table.add_column("Required Config")

    providers = [
        (
            OracleApiType.OPENAI.value,
            "OpenAI GPT models",
            "api_key, model",
        ),
        (
            OracleApiType.AZURE.value,
            "Azure OpenAI Service",
            "api_key, base_url, api_version",
        ),
        (
            OracleApiType.ANTHROPIC.value,
            "Anthropic Claude models",
            "api_key, model",
        ),
        (
            OracleApiType.GEMINI.value,
            "Google Gemini models",
            "api_key, model",
        ),
        (
            OracleApiType.OLLAMA.value,
            "Local Ollama instance",
            "base_url (default: localhost:11434)",
        ),
        (
            OracleApiType.HUMAN.value,
            "Human operator via stdin",
            "none",
        ),
    ]
    for api_type, desc, config in providers:
        table.add_row(api_type, desc, config)
    console.print(table)


@app.command()
def version() -> None:
    """Show the installed GenesisPantheon version."""
    from genesis_pantheon import __version__

    console.print(
        f"[bold]GenesisPantheon[/bold] version [cyan]{__version__}[/cyan]"
    )


if __name__ == "__main__":
    app()
