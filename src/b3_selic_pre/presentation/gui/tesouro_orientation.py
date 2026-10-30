"""Montagem do texto orientativo das sub-abas do Tesouro Direto."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.presentation.tesouro_orientation_text import (
    ORIENTATION_SECTIONS,
    ORIENTATION_TEXTS,
)

__all__ = [
    "ORIENTATION_SECTIONS",
    "ORIENTATION_TEXTS",
    "build_orientation",
]

Widget = Any
TkModule = Any


def build_orientation(
    parent: Widget, kind: str, tk: TkModule, ttk: TkModule
) -> Widget:
    """Build a read-only text box describing the sub-tab."""
    frame = ttk.Frame(parent, padding=(8, 6))
    text = tk.Text(
        frame,
        wrap=tk.WORD,
        width=36,
        state=tk.DISABLED,
        font=("TkDefaultFont", 9),
        padx=6,
        pady=6,
    )
    text.tag_configure("section", font=("TkDefaultFont", 9, "bold"))
    scrollbar = ttk.Scrollbar(
        frame, orient=tk.VERTICAL, command=text.yview
    )
    text.configure(yscrollcommand=scrollbar.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text.configure(state=tk.NORMAL)
    for index, (title, body) in enumerate(
        ORIENTATION_SECTIONS.get(kind, ())
    ):
        if index:
            text.insert(tk.END, "\n\n")
        text.insert(tk.END, f"{title}:", "section")
        text.insert(tk.END, f"\n{body}")
    text.configure(state=tk.DISABLED)
    return frame
