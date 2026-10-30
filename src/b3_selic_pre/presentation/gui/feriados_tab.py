"""Aba ``Feriados`` com árvore ano/mês/dia e textbox somente leitura."""

from __future__ import annotations

import threading
from typing import Any

from b3_selic_pre.presentation.feriados_controller import FeriadosController
from b3_selic_pre.presentation.feriados_view_model import EMPTY_TEXT
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies
from b3_selic_pre.presentation.gui.tooltip import Tooltip

Widget = Any


class FeriadosTab:
    """Exibe o calendário em cache e permite atualização forçada."""

    def __init__(
        self: FeriadosTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
        icons: dict[str, Any],
    ) -> None:
        """Build the tab widgets and load only the local calendar cache."""
        import tkinter as tk
        from tkinter import ttk

        self.frame = parent
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.icons = icons
        self._closed = False
        self._loading = False
        self.controller = self._controller(dependencies)
        self._build_header()
        self._build_body()
        self._build_statusbar()
        self._render_model()

    @staticmethod
    def _controller(
        dependencies: GuiDependencies,
    ) -> FeriadosController | None:
        cache = dependencies.holiday_cache
        service = dependencies.calendar_service
        if cache is None or service is None:
            return None
        return FeriadosController(cache, service)

    def _build_header(self: FeriadosTab) -> None:
        tk, ttk = self.tk, self.ttk
        header = ttk.Frame(self.frame, padding=(8, 6))
        header.pack(fill=tk.X)
        self.refresh_button = ttk.Button(
            header,
            image=self.icons.get("view-refresh", ""),
            text="" if self.icons.get("view-refresh") else "Atualizar",
            command=self._start_refresh,
        )
        self.refresh_button.pack(side=tk.LEFT)
        ttk.Label(
            header, text="Calendário de feriados da ANBIMA"
        ).pack(side=tk.LEFT, padx=(8, 0))
        self.source_var = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.source_var).pack(side=tk.RIGHT)
        Tooltip(
            self.refresh_button,
            "Atualiza o calendário de feriados da ANBIMA",
        )

    def _build_body(self: FeriadosTab) -> None:
        tk, ttk = self.tk, self.ttk
        paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        tree_frame = ttk.Frame(paned)
        text_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=2)
        paned.add(text_frame, weight=3)
        self.tree = ttk.Treeview(tree_frame, show="tree")
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        Tooltip(
            self.tree,
            "Selecione ano, mês ou dia para ver os feriados",
        )
        self.text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.text.pack(fill=tk.BOTH, expand=True)

    def _build_statusbar(self: FeriadosTab) -> None:
        tk, ttk = self.tk, self.ttk
        self.status_var = tk.StringVar(value="")
        ttk.Label(
            self.frame, textvariable=self.status_var, padding=(8, 2)
        ).pack(fill=tk.X)

    def _render_model(self: FeriadosTab) -> None:
        model = self.controller.model if self.controller else None
        for item in self.tree.get_children(""):
            self.tree.delete(item)
        self.source_var.set("")
        if model is None or model.is_empty:
            self._set_text(EMPTY_TEXT)
            self.status_var.set(EMPTY_TEXT)
            return
        for row in model.rows:
            parent = row.parent if row.parent else ""
            self.tree.insert(parent, "end", iid=row.iid, text=row.text)
        self._set_text(model.text_for(model.years[0].iid))
        self.status_var.set(
            f"Feriados em cache: {', '.join(str(y.year) for y in model.years)}"
        )

    def _set_text(self: FeriadosTab, content: str) -> None:
        self.text.configure(state=self.tk.NORMAL)
        self.text.delete("1.0", self.tk.END)
        self.text.insert("1.0", content)
        self.text.configure(state=self.tk.DISABLED)

    def _on_select(self: FeriadosTab, _event: object = None) -> None:
        selection = self.tree.selection()
        if not selection or self.controller is None:
            return
        self._set_text(self.controller.model.text_for(selection[0]))

    def _displayed_years(self: FeriadosTab) -> tuple[int, ...]:
        if self.controller is None:
            return ()
        return tuple(year.year for year in self.controller.model.years)

    def _start_refresh(self: FeriadosTab) -> None:
        if self.controller is None or self._loading:
            return
        self._loading = True
        self.refresh_button.configure(
            state=self.tk.DISABLED,
            image=self.icons.get("content-loading", ""),
        )
        self.status_var.set("Atualizando calendário de feriados…")
        selection = self.tree.selection()
        previous = selection[0] if selection else None
        years = self._displayed_years()

        def worker() -> None:
            try:
                outcome = self.controller.refresh(years)
            except Exception as exc:
                self.root.after(
                    0, lambda error=exc: self._finish_refresh(None, previous, error)
                )
                return
            self.root.after(
                0, lambda: self._finish_refresh(outcome, previous, None)
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_refresh(
        self: FeriadosTab,
        outcome: object | None,
        previous: str | None,
        error: Exception | None,
    ) -> None:
        if self._closed:
            return
        self._loading = False
        self.refresh_button.configure(
            state=self.tk.NORMAL,
            image=self.icons.get("view-refresh", ""),
        )
        if error is not None:
            self.status_var.set(f"Falha ao atualizar: {error}")
            return
        if outcome is not None and getattr(outcome, "refreshed", False):
            self._render_model()
            self._restore_selection(previous)
            self.status_var.set("Calendário de feriados atualizado.")
        else:
            failed = getattr(outcome, "failed_years", ())
            self.status_var.set(
                "Falha ao atualizar o calendário"
                + (f": {', '.join(map(str, failed))}" if failed else ".")
            )

    def _restore_selection(self: FeriadosTab, previous: str | None) -> None:
        if self.controller is None or previous is None:
            return
        if self.controller.model.contains(previous):
            self.tree.selection_set(previous)
            self.tree.see(previous)

    def close(self: FeriadosTab) -> None:
        """Mark the tab as closed to drop late callbacks."""
        self._closed = True


__all__ = ["FeriadosTab"]
