#!/usr/bin/env python3
"""PromptCraft Chat — local terminal UI for Claude."""

import json
import os
import sys
from pathlib import Path

try:
    from anthropic import Anthropic, AuthenticationError
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
except ImportError:
    print("Missing dependencies. Run:  pip install anthropic rich")
    sys.exit(1)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

console = Console()

CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "PromptCraft" / "config.json"


def load_api_key() -> str:
    """Return saved API key, or prompt the user and save it."""
    # Check env var first (allows temporary override)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key

    # Load from saved config
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            key = data.get("api_key", "")
            if key:
                return key
        except Exception:
            pass

    # First run — ask the user
    console.print()
    console.print(Panel(
        "Paste your Anthropic API key below.\n"
        "[dim]It will be saved to:[/dim] [yellow]%APPDATA%\\PromptCraft\\config.json[/yellow]\n"
        "[dim]You won't be asked again.[/dim]",
        title="[cyan]First-time setup[/cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    while True:
        key = Prompt.ask("[bold yellow]API Key[/bold yellow]", password=True).strip()
        if key.startswith("sk-"):
            break
        console.print("[red]That doesn't look like a valid key (should start with sk-).[/red] Try again.\n")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"api_key": key}, indent=2))
    console.print("[dim]Key saved.[/dim]\n")
    return key


def header():
    console.clear()
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("PromptCraft Chat\n", "bold cyan"),
            (f"Model: {MODEL}  |  ", "dim"),
            ("exit", "dim yellow"),
            (" to quit  |  ", "dim"),
            ("clear", "dim yellow"),
            (" to reset  |  ", "dim"),
            ("key", "dim yellow"),
            (" to change API key", "dim"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def reset_api_key():
    """Delete saved key and prompt for a new one."""
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    console.print("[dim]Saved key removed. Enter a new one.[/dim]\n")
    return load_api_key()


def run():
    key = load_api_key()
    client = Anthropic(api_key=key)
    history: list[dict] = []

    header()

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("\n[dim]Goodbye.[/dim]\n")
            break

        if user_input.lower() == "clear":
            history.clear()
            header()
            console.print("[dim]Conversation cleared.[/dim]\n")
            continue

        if user_input.lower() == "key":
            key = reset_api_key()
            client = Anthropic(api_key=key)
            continue

        history.append({"role": "user", "content": user_input})

        try:
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=history,
                )
        except AuthenticationError:
            console.print("\n[red]Invalid API key.[/red] Type [yellow]key[/yellow] to enter a new one.\n")
            history.pop()
            continue
        except Exception as exc:
            console.print(f"\n[red]API error:[/red] {exc}\n")
            history.pop()
            continue

        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        console.print()
        console.print("[bold blue]Claude[/bold blue]")
        console.print(Panel(Markdown(reply), border_style="blue", padding=(1, 2)))
        console.print()


if __name__ == "__main__":
    run()
