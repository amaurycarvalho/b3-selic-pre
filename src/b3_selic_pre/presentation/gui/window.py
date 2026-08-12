"""Mixin de gerenciamento de estado e posição da janela da aplicação."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

Event = Any
App = Any


class WindowMixin:
    """Responsável pela centralização, geometria e data útil da janela."""

    def _center_window(self: App) -> None:
        """Centraliza a janela na tela e persiste a geometria resultante."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.update_idletasks()
        self.settings.set("window_geometry", self.root.geometry())

    def _on_window_configure(self: App, event: Event) -> None:
        """Agenda a persistência do estado da janela após cada redimensionamento."""
        if event.widget != self.root:
            return
        if self._configure_after_id:
            self.root.after_cancel(self._configure_after_id)
        self._configure_after_id = self.root.after(500, self._save_window_state)

    def _save_window_state(self: App) -> None:
        """Salva geometria e maximização atuais da janela nas configurações."""
        self._configure_after_id = None
        state = self.root.state()
        is_maximized = state == "zoomed"
        if not is_maximized:
            self.settings.set("window_geometry", self.root.geometry())
        self.settings.set("window_maximized", is_maximized)

    def _nearest_business_day(self: App, date_str: str) -> str:
        """Retorna a data útil mais próxima (retrocede fins de semana)."""
        parsed = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
        while parsed.weekday() >= 5:
            parsed -= timedelta(days=1)
        return parsed.isoformat()

    def _go_today(self: App) -> None:
        """Define a data atual no campo de data e dispara a busca."""
        self.date_var.set(datetime.now(timezone.utc).date().isoformat())
        self.fetch_rates()
