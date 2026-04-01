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
    import pyperclip
except ImportError:
    print("Missing dependencies. Run:  pip install rich pyperclip")
    sys.exit(1)

console = Console()
_session_started = False

SYSTEM_PROMPT = (
    "Answer only what the user asks. "
    "Do not add preamble, unsolicited advice, summaries, or closing remarks. "
    "Be direct and concise."
)


def ask_claude(message: str) -> str:
    global _session_started

    cmd = ["claude", "-p", message, "--output-format", "text"]
    if _session_started:
        cmd.append("--continue")
    else:
        cmd += ["--append-system-prompt", SYSTEM_PROMPT]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        err = result.stderr.strip() or "unknown error"
        raise RuntimeError(err)

    _session_started = True
    return result.stdout.strip()


def reset_session():
    global _session_started
    _session_started = False


def copy(text: str, label: str):
    try:
        pyperclip.copy(text)
        console.print(f"[dim]{label} copied to clipboard.[/dim]\n")
    except Exception:
        console.print("[red]Copy failed — clipboard not available.[/red]\n")


def header():
    console.clear()
    console.print()
    console.print(Panel.fit(
        Text.assemble(
            ("PromptCraft Chat\n", "bold cyan"),
            ("exit", "dim yellow"), (" quit  ", "dim"),
            ("clear", "dim yellow"), (" new chat  ", "dim"),
            ("ca", "dim yellow"), (" copy answer  ", "dim"),
            ("cq", "dim yellow"), (" copy question", "dim"),
        ),
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def run():
    header()

    last_reply = ""
    last_question = ""

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit", "q"):
            console.print("\n[dim]Goodbye.[/dim]\n")
            break

        if cmd == "clear":
            reset_session()
            last_reply = ""
            last_question = ""
            header()
            console.print("[dim]New conversation started.[/dim]\n")
            continue

        if cmd == "ca":
            if last_reply:
                copy(last_reply, "Answer")
            else:
                console.print("[dim]Nothing to copy yet.[/dim]\n")
            continue

        if cmd == "cq":
            if last_question:
                copy(last_question, "Question")
            else:
                console.print("[dim]Nothing to copy yet.[/dim]\n")
            continue

        last_question = user_input

        try:
            with console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                reply = ask_claude(user_input)
        except RuntimeError as exc:
            console.print(f"\n[red]Error:[/red] {exc}\n")
            continue

        last_reply = reply

        console.print()
        console.print("[bold blue]Claude[/bold blue]")
        console.print(Panel(Markdown(reply), border_style="blue", padding=(1, 2)))
        console.print()


if __name__ == "__main__":
    run()
