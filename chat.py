#!/usr/bin/env python3
"""PromptCraft Chat — terminal UI powered by the local `claude` CLI."""

import subprocess
import sys
from datetime import datetime

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
    from rich.align import Align
    from rich.rule import Rule
    from rich import box
    import pyperclip
    import pyfiglet
except ImportError:
    print("Missing dependencies. Run:  pip install rich pyperclip pyfiglet")
    sys.exit(1)

console = Console()
_session_started = False

SYSTEM_PROMPT = (
    "Answer only what the user asks. "
    "Do not add preamble, unsolicited advice, summaries, or closing remarks. "
    "Be direct and concise."
)

LOGO_FONT  = "slant"
ACCENT     = "cyan"
USER_COLOR = "green"
BOT_COLOR  = "bright_blue"
DIM        = "grey50"


# ── helpers ───────────────────────────────────────────────────────────────────

def now() -> str:
    return datetime.now().strftime("%H:%M")


def ask_claude(message: str) -> str:
    global _session_started
    cmd = ["claude", "-p", message, "--output-format", "text"]
    if _session_started:
        cmd.append("--continue")
    else:
        cmd += ["--append-system-prompt", SYSTEM_PROMPT]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "unknown error")
    _session_started = True
    return result.stdout.strip()


def reset_session():
    global _session_started
    _session_started = False


def copy_to_clipboard(text: str, label: str):
    try:
        pyperclip.copy(text)
        console.print(f"\n  [{DIM}]✓ {label} copied to clipboard.[/{DIM}]\n")
    except Exception:
        console.print(f"\n  [red]✗ Copy failed — clipboard not available.[/red]\n")


# ── layout ────────────────────────────────────────────────────────────────────

def draw_logo():
    try:
        art = pyfiglet.figlet_format("PromptCraft", font=LOGO_FONT)
    except Exception:
        art = "  PromptCraft\n"

    lines = art.splitlines()
    text = Text()
    colors = ["cyan", "cyan", "bright_cyan", "bright_cyan", "cyan", "cyan"]
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        text.append(line + "\n", style=f"bold {color}")

    console.print(Align.center(text))
    console.print(
        Align.center(Text("✦  craft prompts · chat with claude · copy answers  ✦", style=DIM))
    )
    console.print()


def draw_shortcuts():
    bar = Text()
    pairs = [
        ("ca", "copy answer"),
        ("cq", "copy question"),
        ("clear", "new chat"),
        ("exit", "quit"),
    ]
    for i, (key, desc) in enumerate(pairs):
        if i:
            bar.append("   ", style=DIM)
        bar.append(f" {key} ", style=f"bold black on {ACCENT}")
        bar.append(f" {desc}", style=DIM)

    console.print(Align.center(bar))
    console.print()
    console.print(Rule(style=DIM))
    console.print()


def header():
    console.clear()
    console.print()
    draw_logo()
    draw_shortcuts()


def draw_user_message(text: str, n: int):
    label = Text()
    label.append(f"  #{n} ", style=DIM)
    label.append("You", style=f"bold {USER_COLOR}")
    label.append(f"  {now()}", style=DIM)
    console.print(label)
    console.print(Panel(
        f"[{USER_COLOR}]{text}[/{USER_COLOR}]",
        border_style=USER_COLOR,
        box=box.ROUNDED,
        padding=(0, 2),
    ))


def draw_claude_message(text: str, n: int):
    label = Text()
    label.append(f"  #{n} ", style=DIM)
    label.append("Claude", style=f"bold {BOT_COLOR}")
    label.append(f"  {now()}", style=DIM)
    console.print(label)
    console.print(Panel(
        Markdown(text),
        border_style=BOT_COLOR,
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()


# ── main loop ─────────────────────────────────────────────────────────────────

def run():
    header()

    last_reply    = ""
    last_question = ""
    msg_count     = 0

    while True:
        try:
            user_input = Prompt.ask(
                f"\n  [bold {USER_COLOR}]›[/bold {USER_COLOR}]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n  [{DIM}]Goodbye.[/{DIM}]\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit", "q"):
            console.print(f"\n  [{DIM}]Goodbye.[/{DIM}]\n")
            break

        if cmd == "clear":
            reset_session()
            last_reply = last_question = ""
            msg_count  = 0
            header()
            continue

        if cmd == "ca":
            copy_to_clipboard(last_reply, "Answer") if last_reply else \
                console.print(f"\n  [{DIM}]Nothing to copy yet.[/{DIM}]\n")
            continue

        if cmd == "cq":
            copy_to_clipboard(last_question, "Question") if last_question else \
                console.print(f"\n  [{DIM}]Nothing to copy yet.[/{DIM}]\n")
            continue

        msg_count    += 1
        last_question = user_input

        console.print()
        draw_user_message(user_input, msg_count)
        console.print()

        try:
            with console.status(
                f"  [{ACCENT}]Claude is thinking...[/{ACCENT}]", spinner="dots"
            ):
                reply = ask_claude(user_input)
        except RuntimeError as exc:
            console.print(f"  [red]Error:[/red] {exc}\n")
            msg_count -= 1
            continue

        last_reply = reply
        draw_claude_message(reply, msg_count)


if __name__ == "__main__":
    run()
