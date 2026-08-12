"""Dica de texto (tooltip) exibida ao passar o cursor sobre widgets Tkinter."""

from __future__ import annotations

from typing import Any

Widget = Any
Event = Any


class Tooltip:
    """Exibe uma dica de texto ao passar o cursor sobre um widget."""

    def __init__(self: Tooltip, widget: Widget, text: str, delay: int = 500) -> None:
        """Configura a dica e vincula os eventos de entrada e saída do cursor."""
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip_window = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _schedule(self: Tooltip, event: Event = None) -> None:
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self: Tooltip) -> None:
        import tkinter as tk
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip_window, text=self.text,
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("TkDefaultFont", 9), padx=4, pady=2,
        )
        label.pack()

    def _hide(self: Tooltip, event: Event = None) -> None:
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None
