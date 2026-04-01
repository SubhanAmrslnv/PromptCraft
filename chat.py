#!/usr/bin/env python3
"""PromptCraft Chat — Textual TUI with clickable buttons."""

import subprocess
import sys
from datetime import datetime

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Static, Input, Button, Markdown
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual import work
    import pyperclip
    import pyfiglet
except ImportError:
    print("Missing dependencies. Run:  pip install textual pyperclip pyfiglet")
    sys.exit(1)

SYSTEM_PROMPT = (
    "Answer only what the user asks. "
    "Do not add preamble, unsolicited advice, summaries, or closing remarks. "
    "Be direct and concise."
)


def make_logo() -> str:
    try:
        return pyfiglet.figlet_format("PromptCraft", font="slant")
    except Exception:
        return "  PromptCraft\n"


def ts() -> str:
    return datetime.now().strftime("%H:%M")


# ── App ───────────────────────────────────────────────────────────────────────

class PromptCraftApp(App):

    CSS = """
    Screen {
        background: #0c0c0c;
        layers: base;
    }

    /* ── header ── */
    #logo {
        content-align: center middle;
        color: cyan;
        text-style: bold;
        padding: 1 4 0 4;
        height: auto;
    }
    #tagline {
        content-align: center middle;
        color: grey35;
        padding: 0 4 1 4;
        height: auto;
    }
    #divider-top {
        height: 1;
        background: grey15;
    }

    /* ── messages ── */
    #messages {
        height: 1fr;
        padding: 0 3;
    }
    .msg-label {
        color: grey35;
        height: auto;
        padding: 1 0 0 0;
    }
    .msg-user {
        background: #0b1f10;
        border: round #245530;
        color: #7be08a;
        padding: 0 2;
        margin: 0 12 0 0;
        height: auto;
    }
    .msg-claude {
        background: #090f1e;
        border: round #1a3a5c;
        color: bright_white;
        padding: 0 2;
        margin: 0 0 0 12;
        height: auto;
    }
    .msg-claude Markdown {
        background: transparent;
        color: bright_white;
    }
    .msg-system {
        color: grey35;
        text-style: italic;
        padding: 0 2;
        height: auto;
        content-align: center middle;
    }

    /* ── input area ── */
    #divider-bottom {
        height: 1;
        background: grey15;
    }
    #input-row {
        height: auto;
        padding: 1 3 0 3;
        align: left middle;
    }
    #user-input {
        width: 1fr;
        background: #161616;
        border: round grey30;
        color: white;
    }
    #user-input:focus {
        border: round cyan;
    }

    /* ── buttons ── */
    #buttons {
        height: auto;
        padding: 1 3 1 3;
        align: left middle;
    }
    Button {
        margin: 0 1 0 0;
        min-width: 18;
        border: tall grey30;
        background: #161616;
        color: grey50;
    }
    Button:hover {
        text-style: bold;
    }
    #btn-copy-answer {
        border: tall #1e5c78;
        background: #071520;
        color: #4aaccc;
    }
    #btn-copy-answer:hover {
        background: #0d2535;
        color: bright_cyan;
    }
    #btn-copy-question {
        border: tall #1e5830;
        background: #071508;
        color: #4acc70;
    }
    #btn-copy-question:hover {
        background: #0d2812;
        color: bright_green;
    }
    #btn-clear {
        border: tall #5c5010;
        background: #151200;
        color: #ccb840;
    }
    #btn-clear:hover {
        background: #252200;
        color: bright_yellow;
    }
    #btn-exit {
        border: tall #5c1a1a;
        background: #150505;
        color: #cc4444;
    }
    #btn-exit:hover {
        background: #250808;
        color: bright_red;
    }
    """

    TITLE = "PromptCraft"

    def __init__(self):
        super().__init__()
        self._session_started = False
        self._last_reply      = ""
        self._last_question   = ""
        self._msg_count       = 0

    # ── layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static(make_logo(), id="logo")
        yield Static(
            "✦  craft prompts · chat with claude · copy answers  ✦",
            id="tagline",
        )
        yield Static("", id="divider-top")
        yield VerticalScroll(id="messages")
        yield Static("", id="divider-bottom")
        with Horizontal(id="input-row"):
            yield Input(
                placeholder="Type your message and press Enter…",
                id="user-input",
            )
        with Horizontal(id="buttons"):
            yield Button("⎘  Copy Answer",   id="btn-copy-answer")
            yield Button("⎘  Copy Question", id="btn-copy-question")
            yield Button("↺  Clear Chat",    id="btn-clear")
            yield Button("✕  Exit",          id="btn-exit")

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()

    # ── message helpers ───────────────────────────────────────────────────────

    def _scroll_end(self):
        self.query_one("#messages", VerticalScroll).scroll_end(animate=False)

    def _append(self, *widgets) -> None:
        container = self.query_one("#messages", VerticalScroll)
        for w in widgets:
            container.mount(w)
        self._scroll_end()

    def _system(self, text: str) -> None:
        self._append(Static(text, classes="msg-system"))

    # ── input handler ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.clear()

        self._msg_count      += 1
        self._last_question   = text
        n = self._msg_count

        self._append(
            Static(
                f"[grey35]#{n}[/grey35]  [bold green]You[/bold green]  [grey35]{ts()}[/grey35]",
                classes="msg-label",
            ),
            Static(text, classes="msg-user"),
            Static("  ···  Claude is thinking", classes="msg-system", id="thinking"),
        )

        self.query_one("#user-input", Input).disabled = True
        self._call_claude(text, n)

    # ── Claude worker ─────────────────────────────────────────────────────────

    @work(thread=True)
    def _call_claude(self, message: str, n: int) -> None:
        cmd = ["claude", "-p", message, "--output-format", "text"]
        if self._session_started:
            cmd.append("--continue")
        else:
            cmd += ["--append-system-prompt", SYSTEM_PROMPT]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                reply   = result.stderr.strip() or "Unknown error"
                success = False
            else:
                reply   = result.stdout.strip()
                success = True
        except Exception as exc:
            reply   = str(exc)
            success = False

        self.call_from_thread(self._on_reply, reply, n, success)

    def _on_reply(self, reply: str, n: int, success: bool) -> None:
        try:
            self.query_one("#thinking").remove()
        except Exception:
            pass

        if success:
            self._session_started = True
            self._last_reply      = reply

        label = Static(
            f"[grey35]#{n}[/grey35]  [bold bright_blue]Claude[/bold bright_blue]  [grey35]{ts()}[/grey35]",
            classes="msg-label",
        )
        msg = Markdown(reply, classes="msg-claude") if success else \
              Static(f"[red]Error:[/red] {reply}", classes="msg-claude")

        self._append(label, msg)

        inp = self.query_one("#user-input", Input)
        inp.disabled = False
        inp.focus()

    # ── button handler ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        if bid == "btn-copy-answer":
            if not self._last_reply:
                self._system("  Nothing to copy yet")
                return
            try:
                pyperclip.copy(self._last_reply)
                self._system("  ✓  Answer copied to clipboard")
            except Exception:
                self._system("  ✗  Copy failed — clipboard not available")

        elif bid == "btn-copy-question":
            if not self._last_question:
                self._system("  Nothing to copy yet")
                return
            try:
                pyperclip.copy(self._last_question)
                self._system("  ✓  Question copied to clipboard")
            except Exception:
                self._system("  ✗  Copy failed — clipboard not available")

        elif bid == "btn-clear":
            self._session_started = False
            self._last_reply      = ""
            self._last_question   = ""
            self._msg_count       = 0
            self.query_one("#messages", VerticalScroll).remove_children()
            self._system("  ↺  Conversation cleared")
            self.query_one("#user-input", Input).focus()

        elif bid == "btn-exit":
            self.exit()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    PromptCraftApp().run()
