#!/usr/bin/env python3
"""PromptCraft Chat — local terminal UI for Claude."""

import os
import sys

try:
    from anthropic import Anthropic
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.text import Text
except ImportError:
    print("Missing dependencies. Run:  pip install anthropic rich")
    sys.exit(1)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

console = Console()


def check_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        console.print()
        console.print(Panel(
            "[red]ANTHROPIC_API_KEY is not set.[/red]\n\n"
            "Add it to your environment before launching:\n\n"
            "  [yellow]set ANTHROPIC_API_KEY=sk-ant-...[/yellow]   [dim](Windows CMD)[/dim]\n"
            "  [yellow]$env:ANTHROPIC_API_KEY='sk-ant-...'[/yellow]  [dim](PowerShell)[/dim]",
            title="Missing API Key",
            border_style="red",
        ))
        console.print()
        sys.exit(1)
    return key


def header():
    console.clear()
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("PromptCraft Chat\n", "bold cyan"),
            (f"Model: {MODEL}  |  Type ", "dim"),
            ("exit", "dim yellow"),
            (" to quit  |  ", "dim"),
            ("clear", "dim yellow"),
            (" to reset", "dim"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def run():
    key = check_api_key()
    client = Anthropic(api_key=key)
    history: list[dict] = []

    header()

    while True:
        # ── user input ──────────────────────────────────────────────────────
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

        history.append({"role": "user", "content": user_input})

        # ── call Claude ──────────────────────────────────────────────────────
        try:
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=history,
                )
        except Exception as exc:
            console.print(f"\n[red]API error:[/red] {exc}\n")
            history.pop()  # remove the failed user message
            continue

        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        # ── render reply ─────────────────────────────────────────────────────
        console.print()
        console.print("[bold blue]Claude[/bold blue]")
        console.print(Panel(
            Markdown(reply),
            border_style="blue",
            padding=(1, 2),
        ))
        console.print()


if __name__ == "__main__":
    run()
