#!/usr/bin/env python3
"""PromptCraft Chat — CustomTkinter GUI"""

import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

try:
    import customtkinter as ctk
    import pyperclip
except ImportError:
    print("Missing dependencies. Run:  pip install customtkinter pyperclip")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

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
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


RULES_FILE = _base_dir() / "rules.md"
CHAT_MODEL = "haiku"

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


# ── App ───────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")


class PromptCraftApp(ctk.CTk):

    # palette
    C_BG     = "#1a1a1a"
    C_BG2    = "#242424"
    C_DIVID  = "#252525"
    C_TEXT   = "#ececec"
    C_DIM    = "#464646"
    C_ORANGE = "#da7756"
    C_GOLD   = "#c8a830"
    C_RED    = "#c84040"
    C_BLUE   = "#6080c8"

    PLACEHOLDER = "Type your message… (Enter to send · Shift+Enter for new line)"

    INFO_TEXT = (
        "/info       Show this help\n"
        "/clear      Start a new conversation\n"
        "ca          Copy Claude's last answer\n"
        "cq          Copy your last question\n"
        "Enter       Send message\n"
        "Shift+Enter New line in input\n"
        "♥ Like      Extract rules from last answer\n"
    )

    def __init__(self) -> None:
        super().__init__()
        self.title("PromptCraft")
        self.geometry("960x720")
        self.minsize(640, 480)
        self.configure(fg_color=self.C_BG)

        try:
            self.iconbitmap(str(_base_dir() / "app.ico"))
        except Exception:
            pass

        self._session_started  = False
        self._last_reply       = ""
        self._last_question    = ""
        self._msg_count        = 0
        self._rules            = load_rules()
        self._input_locked     = False
        self._placeholder_on   = True

        self._build_ui()
        self._input_box.focus_set()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # header
        hdr = ctk.CTkFrame(self, fg_color=self.C_BG, corner_radius=0)
        hdr.pack(fill="x", padx=24, pady=(12, 0))
        ctk.CTkLabel(
            hdr, text="✦  PromptCraft",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.C_ORANGE,
        ).pack()
        ctk.CTkLabel(
            hdr, text="craft prompts · chat with claude · copy answers",
            font=ctk.CTkFont(size=11),
            text_color=self.C_DIM,
        ).pack()

        ctk.CTkFrame(self, height=1, fg_color=self.C_DIVID, corner_radius=0).pack(
            fill="x", pady=(10, 0)
        )

        # messages
        self._msg_box = ctk.CTkTextbox(
            self,
            fg_color=self.C_BG,
            text_color=self.C_TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            wrap="word",
            state="disabled",
            corner_radius=0,
            border_width=0,
            activate_scrollbars=True,
        )
        self._msg_box.pack(fill="both", expand=True, padx=24, pady=(8, 0))

        tb = self._msg_box._textbox
        tb.tag_config("user_lbl",   foreground=self.C_DIM)
        tb.tag_config("claude_lbl", foreground=self.C_ORANGE)
        tb.tag_config("user_msg",   foreground=self.C_TEXT, lmargin1=20, lmargin2=20)
        tb.tag_config("claude_msg", foreground=self.C_TEXT)
        tb.tag_config("system",     foreground=self.C_DIM,
                      font=("Segoe UI", 11, "italic"))
        tb.tag_config("error",      foreground=self.C_RED)

        ctk.CTkFrame(self, height=1, fg_color=self.C_DIVID, corner_radius=0).pack(
            fill="x", pady=(6, 0)
        )

        # input
        inp_wrap = ctk.CTkFrame(self, fg_color=self.C_BG, corner_radius=0)
        inp_wrap.pack(fill="x", padx=24, pady=(8, 0))

        self._input_box = ctk.CTkTextbox(
            inp_wrap,
            height=72,
            fg_color=self.C_BG2,
            text_color=self.C_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            border_color="#383838",
            border_width=1,
            corner_radius=8,
            wrap="word",
        )
        self._input_box.pack(fill="x")
        self._input_box.insert("0.0", self.PLACEHOLDER)

        self._input_box.bind("<FocusIn>",     self._ph_clear)
        self._input_box.bind("<FocusOut>",    self._ph_restore)
        self._input_box.bind("<Shift-Return>", self._on_shift_enter)
        self._input_box.bind("<Return>",       self._on_enter)

        ctk.CTkLabel(
            inp_wrap,
            text="Enter → send  ·  Shift+Enter → new line",
            font=ctk.CTkFont(size=10),
            text_color=self.C_DIM,
        ).pack(anchor="e", pady=(2, 0))

        # buttons
        btn_wrap = ctk.CTkFrame(self, fg_color=self.C_BG, corner_radius=0)
        btn_wrap.pack(fill="x", padx=24, pady=(8, 0))

        base = dict(
            width=92, height=30, corner_radius=6, border_width=0,
            fg_color=self.C_BG2, hover_color="#2e2e2e",
            font=ctk.CTkFont(size=12),
        )
        ctk.CTkButton(btn_wrap, text="↺  Clear", text_color=self.C_GOLD,
                      command=self._do_clear, **base).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_wrap, text="✕  Exit",  text_color=self.C_RED,
                      command=self.destroy, **base).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_wrap, text="ℹ  Info",  text_color=self.C_BLUE,
                      command=self._show_info, **base).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_wrap, text="♥  Like",  text_color=self.C_ORANGE,
                      command=self._like_answer, **base).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_wrap, text="➤  Send", text_color=self.C_ORANGE,
            fg_color="#2a1a10", hover_color="#3a2010",
            font=ctk.CTkFont(size=12), width=80, height=30,
            corner_radius=6, border_width=0,
            command=self._send,
        ).pack(side="right")

        # copy cards
        cards = ctk.CTkFrame(self, fg_color=self.C_BG, corner_radius=0)
        cards.pack(fill="x", padx=24, pady=(8, 14))
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        self._card_q = ctk.CTkButton(
            cards, text="Question\n—",
            fg_color="#212121", hover_color="#201610",
            text_color="#7a5e38", font=ctk.CTkFont(size=11),
            height=52, corner_radius=8,
            border_width=1, border_color="#3a2e1c",
            command=lambda: self._copy(self._last_question, "Question"),
        )
        self._card_q.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._card_a = ctk.CTkButton(
            cards, text="Answer\n—",
            fg_color="#212121", hover_color="#101420",
            text_color="#3c4468", font=ctk.CTkFont(size=11),
            height=52, corner_radius=8,
            border_width=1, border_color="#22263a",
            command=lambda: self._copy(self._last_reply, "Answer"),
        )
        self._card_a.grid(row=0, column=1, sticky="ew")

    # ── placeholder ───────────────────────────────────────────────────────────

    def _ph_clear(self, _=None) -> None:
        if self._placeholder_on:
            self._input_box.delete("0.0", "end")
            self._input_box.configure(text_color=self.C_TEXT)
            self._placeholder_on = False

    def _ph_restore(self, _=None) -> None:
        if not self._input_box.get("0.0", "end").strip():
            self._input_box.configure(text_color=self.C_DIM)
            self._input_box.insert("0.0", self.PLACEHOLDER)
            self._placeholder_on = True

    def _get_input(self) -> str:
        if self._placeholder_on:
            return ""
        return self._input_box.get("0.0", "end").strip()

    def _clear_input(self) -> None:
        self._input_box.delete("0.0", "end")
        self._placeholder_on = False

    # ── key bindings ──────────────────────────────────────────────────────────

    def _on_enter(self, event) -> str:
        self._send()
        return "break"

    def _on_shift_enter(self, event) -> str:
        self._input_box._textbox.insert("insert", "\n")
        return "break"

    # ── send ──────────────────────────────────────────────────────────────────

    def _send(self) -> None:
        if self._input_locked:
            return
        text = self._get_input()
        if not text:
            return
        self._clear_input()

        if text.lower() == "/info":
            self._append_system(self.INFO_TEXT)
            return
        if text.lower() == "/clear":
            self._do_clear()
            return
        if text.lower() == "ca":
            self._copy(self._last_reply, "Answer")
            return
        if text.lower() == "cq":
            self._copy(self._last_question, "Question")
            return

        self._msg_count    += 1
        self._last_question = text
        preview = text[:50] + ("…" if len(text) > 50 else "")
        self._card_q.configure(text=f"Question\n{preview}")

        self._append_user(text)
        self._start_thinking()

        self._input_locked = True
        self._input_box.configure(state="disabled")
        threading.Thread(target=self._call_claude, args=(text,), daemon=True).start()

    # ── message display ───────────────────────────────────────────────────────

    def _write(self, text: str, tag: str = "") -> None:
        self._msg_box.configure(state="normal")
        self._msg_box._textbox.insert("end", text, tag)
        self._msg_box.configure(state="disabled")
        self._msg_box.see("end")

    def _append_user(self, text: str) -> None:
        self._write(f"\nYou  {ts()}\n", "user_lbl")
        self._write(text + "\n", "user_msg")

    def _start_thinking(self) -> None:
        tb = self._msg_box._textbox
        self._msg_box.configure(state="normal")
        tb.mark_set("thinking_start", "end")
        tb.mark_gravity("thinking_start", "left")
        self._msg_box.configure(state="disabled")
        self._write("\n···  Thinking…\n", "system")

    def _finish_thinking(self) -> None:
        try:
            self._msg_box.configure(state="normal")
            self._msg_box._textbox.delete("thinking_start", "end")
            self._msg_box.configure(state="disabled")
        except Exception:
            pass

    def _append_claude(self, text: str, success: bool) -> None:
        self._write(f"\n✦  Claude  {ts()}\n", "claude_lbl")
        if success:
            self._write(text + "\n", "claude_msg")
        else:
            self._write("Error: " + text + "\n", "error")

    def _append_system(self, text: str) -> None:
        self._write("\n" + text + "\n", "system")

    # ── Claude worker ─────────────────────────────────────────────────────────

    def _call_claude(self, message: str) -> None:
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
                reply, success = result.stderr.strip() or "Unknown error", False
            else:
                reply, success = result.stdout.strip(), True
        except Exception as exc:
            reply, success = str(exc), False

        self.after(0, self._on_reply, reply, success)

    def _on_reply(self, reply: str, success: bool) -> None:
        self._finish_thinking()

        if success:
            self._session_started = True
            self._last_reply      = reply
            preview = reply[:50] + ("…" if len(reply) > 50 else "")
            self._card_a.configure(text=f"Answer\n{preview}")

        self._append_claude(reply, success)

        self._input_locked = False
        self._input_box.configure(state="normal")
        self._input_box.focus_set()

    # ── like / rule extraction ────────────────────────────────────────────────

    def _like_answer(self) -> None:
        if not self._last_reply:
            self._append_system("  Nothing to like yet")
            return
        self._append_system("  ♥  Analyzing answer — extracting rules…")
        threading.Thread(
            target=self._extract_rules, args=(self._last_reply,), daemon=True
        ).start()

    def _extract_rules(self, answer: str) -> None:
        prompt = ANALYZE_PROMPT.format(answer=answer)
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", CHAT_MODEL, "--output-format", "text"],
            capture_output=True, text=True,
        )
        rules = result.stdout.strip() if result.returncode == 0 else ""
        self.after(0, self._on_rules_saved, rules)

    def _on_rules_saved(self, rules: str) -> None:
        if not rules:
            self._append_system("  ✗  Could not extract rules — try again")
            return
        append_rules(rules)
        self._rules = load_rules()
        lines = "\n".join(f"     {line}" for line in rules.splitlines())
        self._append_system(f"  ✓  Rules learned and saved:\n{lines}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _copy(self, text: str, label: str) -> None:
        if not text:
            self._append_system("  Nothing to copy yet")
            return
        try:
            pyperclip.copy(text)
            self._append_system(f"  ✓  {label} copied to clipboard")
        except Exception:
            self._append_system("  ✗  Copy failed — clipboard not available")

    def _do_clear(self) -> None:
        self._session_started = False
        self._last_reply      = ""
        self._last_question   = ""
        self._msg_count       = 0
        self._msg_box.configure(state="normal")
        self._msg_box.delete("0.0", "end")
        self._msg_box.configure(state="disabled")
        self._card_q.configure(text="Question\n—")
        self._card_a.configure(text="Answer\n—")
        self._append_system("  ↺  Conversation cleared")
        self._ph_restore()
        self._input_box.focus_set()

    def _show_info(self) -> None:
        self._append_system(self.INFO_TEXT)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = PromptCraftApp()
    app.mainloop()
