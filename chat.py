#!/usr/bin/env python3
"""PromptCraft Chat — Textual TUI with clickable buttons."""

import ctypes
import ctypes.wintypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Static, Input, Button, Markdown
    from textual.containers import Horizontal, VerticalScroll
    from textual import work
    import pyperclip
except ImportError:
    print("Missing dependencies. Run:  pip install textual pyperclip")
    sys.exit(1)

SYSTEM_PROMPT_BASE = """\
Answer only what the user asks. Be direct and concise.

Structure EVERY response using these four XML blocks — no exceptions:

<context>
  One or two sentences: what system, codebase, or domain is in scope.
</context>

<rule>
  The constraints, conventions, or rules that govern the answer.
  Use named subsections (### Name) when more than three rules apply.
  Write <rule></rule> only if there are genuinely no applicable rules.
</rule>

<input>
  The specific request, restated precisely.
  Name each mode or variant if multiple are valid.
</input>

<output>
  The actual answer — code, steps, explanation, or analysis.
  Follow the exact order required by the task.
</output>

Do not add preamble, summaries, or closing remarks outside these blocks.

When a file path is outside the accessible directory:
- Never present options (Option A / B / C or any lettered/numbered choice list).
- Do not mention sandbox settings, --add-dir, or how to fix access.
- Ask directly: one sentence of context, then a numbered list of exactly what code to paste.\
"""

def _base_dir() -> Path:
    """Folder next to the exe when frozen, or next to this script in dev."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


RULES_FILE  = _base_dir() / "rules.md"
CHAT_MODEL  = "haiku"   # alias: haiku | sonnet | opus  (haiku = fastest, no extended thinking)

ANALYZE_PROMPT = (
    "Analyze the following assistant answer. "
    "Extract 1–3 concise, actionable rules (one sentence each) that capture what made this answer good. "
    "These rules will be added to the assistant's system prompt to improve future answers. "
    "Output ONLY the rules, one per line, starting with '- '. No explanations, no preamble.\n\n"
    "Answer:\n{answer}"
)


def load_rules() -> str:
    try:
        return RULES_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def append_rules(new_rules: str) -> None:
    existing = load_rules()
    combined = (existing + "\n" + new_rules).strip()
    RULES_FILE.write_text(combined, encoding="utf-8")


def ts() -> str:
    return datetime.now().strftime("%H:%M")


# ── Copy Card ─────────────────────────────────────────────────────────────────

class CopyCard(Static):
    """Clickable card that shows a content preview and copies to clipboard."""

    can_focus = True

    def __init__(self, label: str, card_id: str) -> None:
        super().__init__(id=card_id)
        self._label   = label
        self._content = ""
        self._refresh_display()

    # ── public ────────────────────────────────────────────────────────────────

    def set_content(self, text: str) -> None:
        self._content = text
        self._refresh_display()

    # ── internal ──────────────────────────────────────────────────────────────

    def _refresh_display(self) -> None:
        preview = self._content
        if len(preview) > 60:
            preview = preview[:60] + "…"
        if not preview:
            preview = "—"
        self.update(
            f"[bold]{self._label}[/bold]\n"
            f"[dim]{preview}[/dim]"
        )

    def _show_feedback(self, ok: bool) -> None:
        icon = "✓  Copied!" if ok else "✗  Failed"
        color = "green" if ok else "red"
        self.update(f"[bold]{self._label}[/bold]\n[{color}]{icon}[/{color}]")
        self.set_timer(1.5, self._refresh_display)

    # ── events ────────────────────────────────────────────────────────────────

    def on_click(self) -> None:
        if not self._content:
            return
        try:
            pyperclip.copy(self._content)
            self._show_feedback(ok=True)
        except Exception:
            self._show_feedback(ok=False)


# ── App ───────────────────────────────────────────────────────────────────────

class PromptCraftApp(App):

    CSS = """
    Screen {
        background: #1a1a1a;
    }

    /* ── header ── */
    #logo {
        content-align: center middle;
        color: #da7756;
        text-style: bold;
        padding: 1 4 0 4;
        height: 2;
    }
    #tagline {
        content-align: center middle;
        color: #444444;
        padding: 0 4 1 4;
        height: 1;
    }
    #divider-top {
        height: 1;
        background: #252525;
    }

    /* ── messages ── */
    #messages {
        height: 1fr;
        padding: 0 4;
    }
    .msg-label {
        color: #464646;
        height: auto;
        padding: 1 0 0 0;
    }
    .msg-user {
        background: #2c2c2c;
        border: round #3a3a3a;
        color: #ececec;
        padding: 0 2;
        margin: 0 0 0 20;
        height: auto;
    }
    .msg-claude {
        background: transparent;
        color: #ececec;
        padding: 0 2;
        margin: 0 20 0 0;
        height: auto;
    }
    .msg-claude Markdown {
        background: transparent;
        color: #ececec;
    }
    .msg-system {
        color: #464646;
        text-style: italic;
        padding: 0 2;
        height: auto;
        content-align: center middle;
    }

    /* ── input area ── */
    #divider-bottom {
        height: 1;
        background: #252525;
    }
    #input-row {
        height: auto;
        padding: 1 4 0 4;
        align: left middle;
    }
    #user-input {
        width: 1fr;
        background: #242424;
        border: round #383838;
        color: #ececec;
    }
    #user-input:focus {
        border: round #da7756;
    }

    /* ── action buttons ── */
    #buttons {
        height: auto;
        padding: 1 4 0 4;
        align: left middle;
    }
    Button {
        margin: 0 1 0 0;
        min-width: 12;
        border: none;
        background: #242424;
        color: #585858;
    }
    Button:hover {
        background: #2e2e2e;
        color: #dadada;
    }
    #btn-clear {
        color: #7a6830;
    }
    #btn-clear:hover {
        background: #26200e;
        color: #c8a830;
    }
    #btn-exit {
        color: #7a3030;
    }
    #btn-exit:hover {
        background: #261414;
        color: #c84040;
    }
    #btn-info {
        color: #38507a;
    }
    #btn-info:hover {
        background: #12182a;
        color: #6080c8;
    }
    #btn-like {
        color: #9a4a30;
    }
    #btn-like:hover {
        background: #261810;
        color: #da7756;
    }

    /* ── copy cards ── */
    #cards {
        height: 5;
        padding: 1 4 1 4;
    }
    CopyCard {
        height: 4;
        padding: 0 2;
        border: round #2e2e2e;
        background: #212121;
        color: #484848;
    }
    CopyCard:hover {
        border: round #3a3a3a;
        color: #dadada;
    }
    #card-question {
        width: 1fr;
        margin: 0 1 0 0;
        border: round #3a2e1c;
        color: #7a5e38;
    }
    #card-question:hover {
        border: round #da7756;
        color: #da9870;
        background: #201610;
    }
    #card-answer {
        width: 1fr;
        border: round #22263a;
        color: #3c4468;
    }
    #card-answer:hover {
        border: round #4a5898;
        color: #7888c8;
        background: #101420;
    }
    """

    TITLE = "PromptCraft"

    INFO = """\
[bold cyan]/info[/bold cyan]      Show this help message

[bold cyan]/clear[/bold cyan]     Start a new conversation — wipes history and resets the session

[bold cyan]ca[/bold cyan]         Copy Claude's last answer to the clipboard

[bold cyan]cq[/bold cyan]         Copy your last question to the clipboard

[bold cyan]Question[/bold cyan]   Card (bottom left)  — click to copy your last question

[bold cyan]Answer[/bold cyan]     Card (bottom right) — click to copy Claude's last answer

[bold cyan]↺ Clear[/bold cyan]    Button — same as typing [bold cyan]/clear[/bold cyan]

[bold cyan]✕ Exit[/bold cyan]     Button — close the application

[bold cyan]ℹ Info[/bold cyan]     Button — show this help

[bold cyan]♥ Like[/bold cyan]     Button — analyze Claude's last answer and extract rules into the system prompt

[dim]Anything else is sent to Claude as a message.[/dim]\
"""

    def __init__(self):
        super().__init__()
        self._session_started = False
        self._last_reply      = ""
        self._last_question   = ""
        self._msg_count       = 0
        self._rules           = load_rules()

    # ── layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("✦  PromptCraft", id="logo")
        yield Static("craft prompts · chat with claude · copy answers", id="tagline")
        yield Static("", id="divider-top")
        yield VerticalScroll(id="messages")
        yield Static("", id="divider-bottom")
        with Horizontal(id="input-row"):
            yield Input(
                placeholder="Type your message and press Enter…",
                id="user-input",
            )
        with Horizontal(id="buttons"):
            yield Button("↺  Clear", id="btn-clear")
            yield Button("✕  Exit",  id="btn-exit")
            yield Button("ℹ  Info",  id="btn-info")
            yield Button("♥  Like",  id="btn-like")
        with Horizontal(id="cards"):
            yield CopyCard("Question", card_id="card-question")
            yield CopyCard("Answer",   card_id="card-answer")

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

        if text.lower() == "/info":
            self._append(Static(self.INFO, classes="msg-system"))
            return

        if text.lower() == "ca":
            self._copy(self._last_reply, "Answer")
            return

        if text.lower() == "cq":
            self._copy(self._last_question, "Question")
            return

        if text.lower() == "/clear":
            self._do_clear()
            return

        self._msg_count    += 1
        self._last_question = text
        n = self._msg_count

        self.query_one("#card-question", CopyCard).set_content(text)

        self._append(
            Static(
                f"[#ececec]You[/#ececec]  [#464646]{ts()}[/#464646]",
                classes="msg-label",
            ),
            Static(text, classes="msg-user"),
            Static("  [#464646]···  Thinking…[/#464646]", classes="msg-system", id="thinking"),
        )

        self.query_one("#user-input", Input).disabled = True
        self._call_claude(text, n)

    # ── Claude worker ─────────────────────────────────────────────────────────

    @work(thread=True)
    def _call_claude(self, message: str, n: int) -> None:
        cmd = ["claude", "-p", message, "--model", CHAT_MODEL, "--output-format", "text"]
        if self._session_started:
            cmd.append("--continue")
        else:
            system_prompt = SYSTEM_PROMPT_BASE
            if self._rules:
                system_prompt += "\n\nAdditional rules learned from liked answers:\n" + self._rules
            cmd += ["--append-system-prompt", system_prompt]

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
            self.query_one("#card-answer", CopyCard).set_content(reply)

        label = Static(
            f"[#da7756]✦[/#da7756]  [#ececec]Claude[/#ececec]  [#464646]{ts()}[/#464646]",
            classes="msg-label",
        )
        msg = Markdown(reply, classes="msg-claude") if success else \
              Static(f"[red]Error:[/red] {reply}", classes="msg-claude")

        self._append(label, msg)

        inp = self.query_one("#user-input", Input)
        inp.disabled = False
        inp.focus()

    # ── like / rule extraction ────────────────────────────────────────────────

    def _like_answer(self) -> None:
        if not self._last_reply:
            self._system("  Nothing to like yet")
            return
        self._system("  ♥  Analyzing answer — extracting rules…")
        self._extract_rules(self._last_reply)

    @work(thread=True)
    def _extract_rules(self, answer: str) -> None:
        prompt = ANALYZE_PROMPT.format(answer=answer)
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", CHAT_MODEL, "--output-format", "text"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            rules = result.stdout.strip()
        else:
            rules = ""
        self.call_from_thread(self._on_rules_saved, rules)

    def _on_rules_saved(self, rules: str) -> None:
        if not rules:
            self._system("  ✗  Could not extract rules — try again")
            return
        append_rules(rules)
        self._rules = load_rules()
        self._system(
            f"  ✓  Rules learned and saved:\n"
            + "\n".join(f"     {line}" for line in rules.splitlines())
        )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _copy(self, text: str, label: str) -> None:
        if not text:
            self._system(f"  Nothing to copy yet")
            return
        try:
            pyperclip.copy(text)
            self._system(f"  ✓  {label} copied to clipboard")
        except Exception:
            self._system("  ✗  Copy failed — clipboard not available")

    def _do_clear(self) -> None:
        self._session_started = False
        self._last_reply      = ""
        self._last_question   = ""
        self._msg_count       = 0
        self.query_one("#messages", VerticalScroll).remove_children()
        self.query_one("#card-question", CopyCard).set_content("")
        self.query_one("#card-answer",   CopyCard).set_content("")
        self._system("  ↺  Conversation cleared")
        self.query_one("#user-input", Input).focus()

    # ── button handler ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if   bid == "btn-clear": self._do_clear()
        elif bid == "btn-info":  self._append(Static(self.INFO, classes="msg-system"))
        elif bid == "btn-exit":  self.exit()
        elif bid == "btn-like":  self._like_answer()


# ── console font ─────────────────────────────────────────────────────────────

class _COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

class _CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize",      ctypes.wintypes.ULONG),
        ("nFont",       ctypes.wintypes.DWORD),
        ("dwFontSize",  _COORD),
        ("FontFamily",  ctypes.wintypes.UINT),
        ("FontWeight",  ctypes.wintypes.UINT),
        ("FaceName",    ctypes.c_wchar * 32),
    ]

def set_console_font_size(pt: int) -> None:
    try:
        handle = ctypes.windll.kernel32.GetStdHandle(ctypes.wintypes.DWORD(-11))
        font = _CONSOLE_FONT_INFOEX()
        font.cbSize = ctypes.sizeof(_CONSOLE_FONT_INFOEX)
        ctypes.windll.kernel32.GetCurrentConsoleFontEx(handle, False, ctypes.byref(font))
        font.dwFontSize.X = 0
        font.dwFontSize.Y = pt
        ctypes.windll.kernel32.SetCurrentConsoleFontEx(handle, False, ctypes.byref(font))
    except Exception:
        pass


# ── taskbar icon ─────────────────────────────────────────────────────────────

def _make_app_icon() -> None:
    """Write app.ico (32×32 RGBA PNG-in-ICO) next to the exe/script if absent.

    Design: six-spoke asterisk in Claude orange (#da7756) on dark (#1a1a1a).
    Uses only stdlib — no Pillow required.
    """
    try:
        import math, struct, zlib

        ico_path = _base_dir() / "app.ico"
        if ico_path.exists():
            return

        SIZE   = 32
        BG     = (0x1a, 0x1a, 0x1a, 0xff)
        FG     = (0xda, 0x77, 0x56, 0xff)
        cx = cy = SIZE / 2
        R_MAX   = 13.5
        R_MIN   = 2.8
        HALF_W  = 2.1
        SPOKES  = 6

        pixels = []
        for y in range(SIZE):
            row = []
            for x in range(SIZE):
                dx, dy = x - cx + 0.5, y - cy + 0.5
                r = math.hypot(dx, dy)
                color = BG
                if R_MIN <= r <= R_MAX:
                    for i in range(SPOKES):
                        a = math.pi * i / SPOKES
                        perp = abs(-dx * math.sin(a) + dy * math.cos(a))
                        if perp < HALF_W:
                            color = FG
                            break
                row.append(color)
            pixels.append(row)

        def _chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        ihdr = struct.pack(">II", SIZE, SIZE) + bytes([8, 6, 0, 0, 0])
        raw  = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)
        png  = (
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw))
            + _chunk(b"IEND", b"")
        )
        ico = (
            struct.pack("<HHH", 0, 1, 1)
            + struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(png), 22)
            + png
        )
        ico_path.write_bytes(ico)
    except Exception:
        pass


def _set_taskbar_icon() -> None:
    """Load app.ico and apply it to the console window (small + large slots)."""
    try:
        ico_path = str(_base_dir() / "app.ico")
        hIcon = ctypes.windll.user32.LoadImageW(
            None, ico_path,
            1,           # IMAGE_ICON
            0, 0,
            0x10,        # LR_LOADFROMFILE
        )
        if not hIcon:
            return
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hIcon)   # ICON_SMALL
            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hIcon)   # ICON_BIG
    except Exception:
        pass


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    set_console_font_size(16)
    _make_app_icon()
    _set_taskbar_icon()
    PromptCraftApp().run()
