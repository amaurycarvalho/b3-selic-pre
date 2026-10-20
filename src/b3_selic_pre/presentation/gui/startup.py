"""Escudo visual e bloqueio de interação durante a inicialização da GUI."""

from __future__ import annotations

from typing import Any

Event = Any
Widget = Any

SETTLE_MS = 200
SHIELD_MESSAGE = "Aguarde a inicialização da aplicação…"
SHIELD_BACKGROUND = "#d9d9d9"


class StartupShield:
    """Cobre a janela e bloqueia teclado enquanto a interface é construída."""

    def __init__(self: StartupShield, root: Widget) -> None:
        """Keep the root window reference for the shield lifecycle."""
        self.root = root
        self.frame = None
        self.label = None

    def show(self: StartupShield) -> None:
        """Create, paint and focus the opaque shield."""
        from tkinter import ttk

        style = ttk.Style(self.root)
        style.configure("StartupShield.TFrame", background=SHIELD_BACKGROUND)
        style.configure("StartupShield.TLabel", background=SHIELD_BACKGROUND)
        self.frame = ttk.Frame(
            self.root, style="StartupShield.TFrame", takefocus=True
        )
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.label = ttk.Label(
            self.frame,
            text=SHIELD_MESSAGE,
            style="StartupShield.TLabel",
            anchor="center",
        )
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        self.frame.bind("<KeyPress>", self._block_event)
        self.frame.bind("<Tab>", self._block_event)
        self.frame.bind("<Shift-Tab>", self._block_event)
        self.frame.bind("<ISO_Left_Tab>", self._block_event)
        self.frame.lift()
        self.root.update_idletasks()
        self.frame.focus_set()

    def raise_above_siblings(self: StartupShield) -> None:
        """Raise the shield above widgets created after it."""
        if self.frame is None:
            return
        try:
            if self.frame.winfo_exists():
                self.frame.lift()
        except Exception:
            return

    def destroy(self: StartupShield) -> None:
        """Destroy the shield widgets and clear references."""
        frame = self.frame
        self.frame = None
        self.label = None
        if frame is None:
            return
        try:
            if frame.winfo_exists():
                frame.destroy()
        except Exception:
            return

    def _block_event(self: StartupShield, event: Event = None) -> str:
        """Swallow keyboard events so focus and shortcuts cannot escape."""
        return "break"
