"""Mixin de barra de status e estados de bloqueio da interface."""

from __future__ import annotations

from typing import Any

App = Any


class StatusMixin:
    """Gerencia mensagens, ícones e bloqueio dos controles da janela."""

    def set_status(self: App, message: str, msg_type: str = "info") -> None:
        """Atualiza a barra de status com a mensagem e cor indicadas."""
        if hasattr(self, "_restore_after_id") and self._restore_after_id:
            self.root.after_cancel(self._restore_after_id)
            self._restore_after_id = None
        icon = self._msg_icons.get(msg_type, "")
        self.status_var.set(f"{icon} {message}" if icon else message)
        color = self._msg_colors.get(msg_type, self._statusbar_default_fg)
        self.statusbar_label.config(foreground=color)

    def _set_ui_locked(self: App, locked: bool, determinate: bool = False) -> None:
        """Habilita ou desabilita os controles durante a busca em segundo plano."""
        state = self.tk.DISABLED if locked else self.tk.NORMAL
        for w in self._lockable_widgets:
            try:
                w.configure(state=state)
            except self.tk.TclError:
                pass
        self.root.config(cursor="watch" if locked else "")
        if locked:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar.pack_forget()
            if determinate:
                self._determinate_bar["value"] = 0
                self._determinate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
            else:
                self._indeterminate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
                self._indeterminate_bar.start()
            self.fetch_button.configure(image=self.icons['content-loading'])
            self.set_status("Buscando taxas…", msg_type="info")
        else:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar.pack_forget()
            self.fetch_button.configure(image=self.icons['view-refresh'])

    def _on_fetch_progress(self: App, current_page: int, total_pages: int | None) -> None:
        """Atualiza a barra de progresso determinada durante a paginação."""
        if total_pages is not None and current_page <= total_pages:
            self._indeterminate_bar.stop()
            self._indeterminate_bar.pack_forget()
            self._determinate_bar["maximum"] = total_pages
            self._determinate_bar["value"] = current_page
            self._determinate_bar.pack(side=self.tk.LEFT, padx=(0, 8))
            self.set_status(
                f"Buscando taxas… ({current_page}/{total_pages} páginas)",
                msg_type="info",
            )

    def _schedule_restore(self: App, prior_text: str, prior_color: str) -> None:
        """Restaura a mensagem anterior da barra de status após alguns segundos."""
        def restore() -> None:
            self.status_var.set(prior_text)
            self.statusbar_label.config(foreground=prior_color)
            self._restore_after_id = None
        self._restore_after_id = self.root.after(2000, restore)
