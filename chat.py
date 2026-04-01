#!/usr/bin/env python3
"""PromptCraft Chat — terminal UI powered by the local `claude` CLI."""

import subprocess
import sys

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
except ImportError:
    print("Missing dependency. Run:  pip install rich")
    sys.exit(1)

console = Console()
_session_started = False


def ask_claude(message: str) -> str:
    global _session_started

    cmd = ["claude", "-p", message, "--output-format", "text"]
    if _session_started:
        cmd.append("--continue")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        err = result.stderr.strip() or "unknown error"
        raise RuntimeError(err)

    _session_started = True
    return result.stdout.strip()


def reset_session():
    global _session_started
    _session_started = False


def header():
    console.clear()
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("PromptCraft Chat\n", "bold cyan"),
            ("Type ", "dim"),
            ("exit", "dim yellow"),
            (" to quit  |  ", "dim"),
            ("clear", "dim yellow"),
            (" to start a new conversation", "dim"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def run():
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
            reset_session()
            header()
            console.print("[dim]New conversation started.[/dim]\n")
            continue

        try:
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                reply = ask_claude(user_input)
        except RuntimeError as exc:
            console.print(f"\n[red]Error:[/red] {exc}\n")
            continue

        console.print()
        console.print("[bold blue]Claude[/bold blue]")
        console.print(Panel(Markdown(reply), border_style="blue", padding=(1, 2)))
        console.print()


if __name__ == "__main__":
    run()