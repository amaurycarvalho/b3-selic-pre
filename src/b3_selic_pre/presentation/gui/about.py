"""Janela modal de informações da aplicação."""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

from b3_selic_pre import __release_date__, __version__
from b3_selic_pre.application.about import (
    AboutInfo,
    build_about_info,
    new_version_notice,
    release_page_url,
)

App = Any
Widget = Any
TkModule = Any

logger = logging.getLogger(__name__)

LOGS_UNAVAILABLE = "Diretório de logs indisponível."
LOGS_OPEN_FAILED = "Não foi possível abrir o diretório de logs."
LINK_OPEN_FAILED = "Não foi possível abrir o link no navegador."


class AboutMixin:
    """Monta o diálogo Sobre e atualiza o aviso de nova versão."""

    def _open_about(self: App) -> None:
        """Open the About dialog, reusing the window when already visible."""
        dialog = getattr(self, "_about_dialog", None)
        if dialog is not None and dialog.winfo_exists():
            dialog.lift()
            dialog.focus_set()
            return
        self._about_dialog = self._build_about_dialog()
        self._start_version_check(self._about_dialog)

    def _build_about_dialog(self: App) -> Widget:
        """Build the modal dialog with identity, links and a notice footer."""
        import tkinter as tk
        from tkinter import ttk

        info = build_about_info(__version__, __release_date__)
        dialog = tk.Toplevel(self.root)
        dialog.title("Sobre")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.protocol("WM_DELETE_WINDOW", self._close_about)
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        self._build_about_header(frame, dialog, info, tk, ttk)
        ttk.Label(
            frame, text=info.description, wraplength=460, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(12, 0))
        self._build_about_actions(frame, dialog, info, tk, ttk)
        footer = ttk.Frame(frame)
        footer.pack(fill=tk.X, pady=(12, 0))
        dialog._about_footer = footer
        dialog._about_message = ttk.Label(footer, text="", foreground="orange")
        dialog._about_message.pack(anchor=tk.W)
        dialog.grab_set()
        return dialog

    def _build_about_header(
        self: App,
        frame: Widget,
        dialog: Widget,
        info: AboutInfo,
        tk: TkModule,
        ttk: TkModule,
    ) -> None:
        """Render the icon, title, release date and license."""
        header = ttk.Frame(frame)
        header.pack(fill=tk.X)
        icon = self._load_about_icon(dialog, tk)
        if icon is not None:
            ttk.Label(header, image=icon).pack(side=tk.LEFT, padx=(0, 12))
        text = ttk.Frame(header)
        text.pack(side=tk.LEFT, fill=tk.X)
        ttk.Label(
            text, text=info.title, font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W)
        ttk.Label(
            text, text=f"Data de lançamento: {info.release_date}"
        ).pack(anchor=tk.W)
        ttk.Label(text, text=f"Licença: {info.license_text}").pack(anchor=tk.W)

    def _load_about_icon(
        self: App, dialog: Widget, tk: TkModule
    ) -> Widget | None:
        """Load and keep the application icon alive for the dialog."""
        path = self.deps.icon_source()
        if not path or not os.path.exists(path):
            return None
        icon = tk.PhotoImage(file=path, master=dialog)
        dialog._about_icon_img = icon
        return icon

    def _build_about_actions(
        self: App,
        frame: Widget,
        dialog: Widget,
        info: AboutInfo,
        tk: TkModule,
        ttk: TkModule,
    ) -> None:
        """Render the repository, log directory and close buttons."""
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(
            actions,
            text="Repositório",
            command=lambda: self._open_about_url(dialog, info.repository_url),
        ).pack(side=tk.LEFT)
        ttk.Button(
            actions,
            text="Diretório de logs",
            command=lambda: self._open_about_logs(dialog),
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            actions,
            text="Fechar",
            command=self._close_about,
        ).pack(side=tk.RIGHT)

    def _open_about_url(self: App, dialog: Widget, url: str) -> None:
        """Open a URL, reporting failures inside the dialog."""
        if not self.deps.open_url(url):
            self._show_about_message(dialog, LINK_OPEN_FAILED)

    def _open_about_logs(self: App, dialog: Widget) -> None:
        """Open the log directory without ever creating it."""
        path = self.deps.log_directory()
        if not path or not os.path.isdir(path):
            self._show_about_message(dialog, LOGS_UNAVAILABLE)
            return
        if not self.deps.open_directory(path):
            self._show_about_message(dialog, LOGS_OPEN_FAILED)

    def _show_about_message(self: App, dialog: Widget, text: str) -> None:
        """Show a local message in the dialog footer."""
        if not dialog.winfo_exists():
            return
        dialog._about_message.configure(text=text)

    def _start_version_check(self: App, dialog: Widget) -> None:
        """Check the latest release once per session in the background."""
        if getattr(self, "_about_version_checked", False):
            self._apply_latest_version(
                dialog, getattr(self, "_about_latest_version", None)
            )
            return
        if getattr(self, "_about_version_checking", False):
            return
        self._about_version_checking = True

        def worker() -> None:
            try:
                latest = self.deps.latest_version()
            except Exception as exc:
                logger.debug("Falha ao verificar nova versão: %s", exc)
                latest = None
            self.root.after(
                0, lambda: self._apply_latest_version(dialog, latest)
            )

        threading.Thread(target=worker, daemon=True).start()

    def _apply_latest_version(
        self: App, dialog: Widget, latest: str | None
    ) -> None:
        """Cache the check result and render the notice when applicable."""
        self._about_version_checking = False
        self._about_version_checked = True
        self._about_latest_version = latest
        if not dialog.winfo_exists():
            return
        notice = new_version_notice(__version__, latest)
        if notice is None:
            return
        self._render_version_notice(dialog, latest, notice)

    def _render_version_notice(
        self: App,
        dialog: Widget,
        latest: str | None,
        notice: str,
    ) -> None:
        """Append the update notice and release button to the footer."""
        from tkinter import ttk

        footer = getattr(dialog, "_about_footer", None)
        if footer is None or not footer.winfo_exists():
            return
        ttk.Label(footer, text=notice, foreground="green").pack(anchor="w")
        ttk.Button(
            footer,
            text="Abrir página da release",
            command=lambda: self._open_about_url(
                dialog, release_page_url(latest)
            ),
        ).pack(anchor="w", pady=(4, 0))

    def _close_about(self: App) -> None:
        """Release the modal grab and discard the dialog reference."""
        dialog = getattr(self, "_about_dialog", None)
        self._about_dialog = None
        if dialog is None or not dialog.winfo_exists():
            return
        dialog.grab_release()
        dialog.destroy()
