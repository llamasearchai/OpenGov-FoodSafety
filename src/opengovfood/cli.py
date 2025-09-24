"""Command-line interface for OpenGov Food."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from sqlalchemy import text

from .core.config import get_settings
from .core.database import (
    DatabaseManager,
    initialize_database_sync,
    seed_database_sync,
)
from .services.agent_service import AgentService
from .services.ollama_service import OllamaService
from .utils.logging import configure_logging, get_logger

console = Console()
logger = get_logger(__name__)

app = typer.Typer(
    name="opengov-food",
    help="Comprehensive consumer protection and food safety inspection management for environmental health departments.",
    add_completion=False,
    rich_markup_mode="rich",
)
agent_app = typer.Typer(help="AI-powered analysis commands", rich_markup_mode="rich")
db_app = typer.Typer(help="Database management commands", rich_markup_mode="rich")
llm_app = typer.Typer(help="Local model lifecycle commands", rich_markup_mode="rich")
status_app = typer.Typer(help="System diagnostics", rich_markup_mode="rich")

app.add_typer(agent_app, name="agent")
app.add_typer(db_app, name="db")
app.add_typer(llm_app, name="llm")
app.add_typer(status_app, name="status")


def run_async(coro: Any) -> Any:
    """Execute an asynchronous coroutine from synchronous command context."""
    return asyncio.run(coro)


def _with_progress(description: str, task: Callable[[], Any]) -> Any:
    """Execute a callable while displaying a spinner progress indicator."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task(description, total=None)
        try:
            result = task()
            return result
        except Exception as exc:  # pragma: no cover - handled by caller
            raise exc
        finally:
            progress.remove_task(task_id)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to alternate configuration file"),
) -> None:
    """Global application configuration."""
    configure_logging(debug=verbose)
    if config:
        os.environ["OPENGOVFOOD_CONFIG_PATH"] = str(config.resolve())
    ctx.obj = {"settings": get_settings()}


@agent_app.command("run")
def agent_run(
    prompt: str = typer.Argument(..., help="Prompt describing the inspection analysis task"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model identifier to use"),
    provider: str = typer.Option("openai", "--provider", "-p", help="Provider name: openai, ollama, or mock"),
) -> None:
    """Run AI-powered inspection analysis."""

    def _execute() -> Dict[str, Any]:
        service = AgentService()
        return run_async(service.run_analysis(prompt=prompt, model=model, provider=provider))

    try:
        result = _with_progress("Executing analysis", _execute)
        console.print("[bold green]Analysis complete[/bold green]")
        console.print_json(data=result)
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Analysis failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@agent_app.command("chat")
def agent_chat(message: str = typer.Argument(..., help="Message for the inspection assistant")) -> None:
    """Interact with the inspection assistant."""

    def _execute() -> str:
        service = AgentService()
        return run_async(service.chat(message))

    try:
        response = _with_progress("Generating response", _execute)
        console.print("[bold green]Assistant response[/bold green]")
        console.print(response)
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Chat failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@db_app.command("init")
def db_init(
    drop_existing: bool = typer.Option(False, "--drop-existing", help="Drop existing schema before creating tables"),
) -> None:
    """Initialise the database schema."""

    def _execute() -> None:
        initialize_database_sync(drop_existing=drop_existing)

    _with_progress("Preparing database", _execute)
    console.print("[bold green]Database initialised[/bold green]")


@db_app.command("seed")
def db_seed() -> None:
    """Populate the database with representative sample data."""

    def _execute() -> None:
        seed_database_sync()

    _with_progress("Seeding database", _execute)
    console.print("[bold green]Sample data created[/bold green]")


@db_app.command("status")
def db_status() -> None:
    """Verify database connectivity."""

    async def _ping() -> str:
        manager = DatabaseManager()
        async with manager.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return "Connection successful"

    try:
        message = _with_progress("Checking database connection", lambda: run_async(_ping()))
        console.print(f"[bold green]{message}[/bold green]")
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Database check failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@llm_app.command("list")
def llm_list() -> None:
    """List available Ollama models."""

    async def _collect() -> Dict[str, Any]:
        service = OllamaService()
        models = await service.list_models()
        return {"models": models}

    try:
        payload = _with_progress("Retrieving model catalogue", lambda: run_async(_collect()))
        models = payload["models"]
        if not models:
            console.print("No Ollama models available.")
            return
        table = Table(title="Ollama Models")
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="white")
        table.add_column("Details", style="white")
        for model in models:
            table.add_row(model.get("name", "Unknown"), str(model.get("size", "")), model.get("details", ""))
        console.print(table)
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Failed to list models:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@llm_app.command("pull")
def llm_pull(model: str = typer.Argument(..., help="Model identifier to download")) -> None:
    """Pull an Ollama model for local inference."""

    async def _pull() -> None:
        service = OllamaService()
        await service.pull_model(model)

    try:
        _with_progress(f"Downloading model {model}", lambda: run_async(_pull()))
        console.print(f"[bold green]Model {model} downloaded[/bold green]")
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Model download failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@llm_app.command("check")
def llm_check() -> None:
    """Verify connectivity to the Ollama service."""

    async def _check() -> bool:
        service = OllamaService()
        return await service.check_connection()

    try:
        available = _with_progress("Checking Ollama endpoint", lambda: run_async(_check()))
        if available:
            console.print("[bold green]Ollama service reachable[/bold green]")
        else:
            console.print("[bold red]Ollama service unavailable[/bold red]")
            raise typer.Exit(code=1)
    except Exception as exc:  # pragma: no cover - CLI surface
        console.print(f"[bold red]Ollama check failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@status_app.command("overview")
def status_overview() -> None:
    """Display system configuration and subsystem health."""

    settings = get_settings()
    config_table = Table(title="Configuration Summary", show_header=True, header_style="bold")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="white")
    config_table.add_row("Project", settings.PROJECT_NAME)
    config_table.add_row("API Base", settings.API_V1_STR)
    config_table.add_row("Database", settings.database_url)
    config_table.add_row("OpenAI Configured", "Yes" if settings.openai_api_key else "No")
    config_table.add_row("Ollama Endpoint", settings.ollama_base_url or "Not set")

    subsystem_table = Table(title="Subsystem Status", show_header=True, header_style="bold")
    subsystem_table.add_column("Subsystem", style="cyan")
    subsystem_table.add_column("Status", style="white")
    subsystem_table.add_column("Details", style="white")

    # Database check
    try:
        async def _check_db():
            async with DatabaseManager().engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return "Connection successful"
        
        message = run_async(_check_db())
        subsystem_table.add_row("Database", "Operational", message)
    except Exception as exc:
        subsystem_table.add_row("Database", "Unavailable", str(exc))

    # Ollama check
    try:
        ollama_available = run_async(OllamaService().check_connection())
        subsystem_table.add_row("Ollama", "Operational" if ollama_available else "Unavailable", "Endpoint ping")
    except Exception as exc:
        subsystem_table.add_row("Ollama", "Error", str(exc))

    # OpenAI check
    subsystem_table.add_row(
        "OpenAI",
        "Configured" if settings.openai_api_key else "Not configured",
        "API key detected" if settings.openai_api_key else "Set OPENAI_API_KEY in environment",
    )

    console.print(config_table)
    console.print(subsystem_table)


@app.command("menu")
def interactive_menu() -> None:
    """Launch an interactive operations menu."""

    menu_actions: Dict[str, Callable[[], None]] = {
        "1": lambda: db_init(drop_existing=False),
        "2": db_seed,
        "3": _menu_run_analysis,
        "4": status_overview,
        "5": lambda: sys.exit(0),
    }

    while True:
        table = Table(title="OpenGov Food Control Centre")
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "Initialise database schema")
        table.add_row("2", "Seed database with sample data")
        table.add_row("3", "Run inspection analysis")
        table.add_row("4", "Show system overview")
        table.add_row("5", "Exit")
        console.print(table)

        selection = typer.prompt("Select an option", default="5").strip()
        action = menu_actions.get(selection)
        if not action:
            console.print("Invalid selection; please choose a valid option.")
            continue
        if selection == "5":
            console.print("Exiting OpenGov Food control centre.")
            action()
            break
        action()


def _menu_run_analysis() -> None:
    """Prompt for analysis parameters in interactive menu."""
    prompt = typer.prompt("Enter analysis prompt")
    model = typer.prompt("Model", default="gpt-4")
    provider = typer.prompt("Provider", default="openai")
    agent_run(prompt=prompt, model=model, provider=provider)


if __name__ == "__main__":
    app()