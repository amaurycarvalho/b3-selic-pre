"""Painel de um gráfico do Tesouro com toolbar vertical, cópia e hover."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from b3_selic_pre.presentation.charts_hover import HoverTooltip

Widget = Any
Canvas = Any
Chart = Any
Toolbar = Any
Render = Callable[[Any, Any], None]
StatusCallback = Callable[[str, str], None]


def _no_status(message: str, msg_type: str) -> None:
    return None


def _vertical_toolbar(canvas: Canvas, window: Widget) -> Toolbar:
    """Create a matplotlib navigation toolbar stacked vertically."""
    import tkinter as tk

    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

    class VerticalToolbar2Tk(NavigationToolbar2Tk):
        def __init__(
            self: VerticalToolbar2Tk, canvas: Canvas, window: Widget
        ) -> None:
            super().__init__(canvas, window, pack_toolbar=False)
            self.pack_propagate(True)
            children = list(self.winfo_children())
            for child in children:
                child.pack_forget()
            for child in children:
                if isinstance(child, (tk.Label, tk.Frame)):
                    continue
                child.pack(side=tk.TOP, anchor=tk.W, pady=1)

    return VerticalToolbar2Tk(canvas, window)


class ChartPanel:
    """Figure, canvas, toolbar vertical, cópia e rótulos de hover."""

    def __init__(
        self: ChartPanel,
        parent: Widget,
        *,
        icons: dict[str, Any],
        on_status: StatusCallback = _no_status,
    ) -> None:
        """Create the panel widgets and its vertical chart toolbar."""
        import tkinter as tk
        from tkinter import ttk

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.icons = icons
        self._on_status = on_status
        self.frame = ttk.Frame(parent)
        body = ttk.Frame(self.frame)
        body.pack(fill=tk.BOTH, expand=True)
        self.toolbar_host = ttk.Frame(body)
        self.toolbar_host.pack(side=tk.LEFT, fill=tk.Y)
        canvas_frame = ttk.Frame(body)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.figure = Figure(figsize=(8, 2.8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = _vertical_toolbar(self.canvas, self.toolbar_host)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        image = icons.get('edit-copy')
        self.copy_button = tk.Button(
            self.toolbar,
            image=image if image is not None else "",
            text="" if image is not None else "Copiar",
            command=self.copy_to_clipboard,
            bd=0,
            relief=tk.FLAT,
        )
        self.copy_button.pack(side=tk.TOP, anchor=tk.W, pady=2)
        self.toolbar.update()
        self.hover = HoverTooltip(self.canvas)

    def draw(self: ChartPanel, render: Render, chart: Chart) -> None:
        """Render the chart data and refresh the canvas."""
        render(self.figure, chart)
        self.canvas.draw_idle()

    def copy_to_clipboard(self: ChartPanel) -> None:
        """Copy the current figure as an image to the clipboard."""
        import io

        import pyxclip
        from PIL import Image

        buffer = io.BytesIO()
        self.figure.savefig(buffer, format="png", dpi=150)
        image = Image.open(buffer).convert("RGBA")
        try:
            pyxclip.copy((image.width, image.height, image.tobytes()))
            self._on_status(
                "Gráfico copiado para a área de transferência.", "success"
            )
        except pyxclip.ClipboardError:
            self._on_status(
                "Use o botão Salvar do toolbar para salvar o gráfico.",
                "warning",
            )
