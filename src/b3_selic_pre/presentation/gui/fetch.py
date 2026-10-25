"""Mixin de busca e tratamento de dados vindos da B3."""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

from b3_selic_pre.application.use_cases import (
    FutureQueryDateError,
    OldQueryDateError,
    nearest_business_day,
    validate_query_date,
)
from b3_selic_pre.domain.constants import EVOLUTION_DAYS
from b3_selic_pre.presentation.gui_reference import record_reference
from b3_selic_pre.presentation.logging_utils import log_exception
from b3_selic_pre.presentation.view_model import historical_status

App = Any

Data = Any

logger = logging.getLogger(__name__)


class FetchMixin:
    """Gerencia a busca de taxas em segundo plano e o tratamento dos resultados."""

    def fetch_rates(self: App) -> None:
        """Busca as taxas para a data informada em segundo plano."""
        try:
            reference_date = validate_query_date(self.date_var.get().strip())
        except FutureQueryDateError as exc:
            self.set_status(str(exc), msg_type="error")
            return
        except OldQueryDateError as exc:
            self.set_status(str(exc), msg_type="warning")
            return
        except ValueError as exc:
            self.set_status(str(exc), msg_type="error")
            return
        reference_date = nearest_business_day(reference_date)
        self.date_var.set(reference_date)
        if self._client is None:
            self.set_status("Cliente de dados não configurado.", msg_type="error")
            return
        self._set_ui_locked(True)
        self._last_reference_date = reference_date
        if self.evolution_var.get():
            self.historical_data = None

        def _source_cb(source: str) -> None:
            self._data_source = source

        def _progress_cb(current: int, total: int) -> None:
            self.root.after(0, lambda: self._on_fetch_progress(current, total))

        def worker() -> None:
            try:
                records = self._client.fetch_rates_for_date(
                    reference_date, force=True, source_callback=_source_cb,
                    page_size=100, progress_callback=_progress_cb,
                )
            except Exception as exc:
                try:
                    log_exception(logger, exc, "Falha ao buscar dados")
                finally:
                    self.root.after(
                        0,
                        lambda error=exc: self.handle_fetch_error(error),
                    )
                return
            self.root.after(0, lambda: self.handle_fetch_success(records))
        threading.Thread(target=worker, daemon=True).start()

    def _fetch_historical_rates(self: App, reference_date: str) -> None:
        """Busca o histórico de taxas dos últimos pregões em segundo plano."""
        if getattr(self, "_historical_fetching", False):
            return
        if self._client is None:
            self.set_status("Cliente de dados não configurado.", msg_type="error")
            return
        self._historical_fetching = True
        self._set_ui_locked(True, determinate=True)
        self._determinate_bar["maximum"] = len(EVOLUTION_DAYS)

        def progress(completed: int, total: int) -> None:
            self.root.after(0, lambda: self._determinate_bar.configure(value=completed))
            self.root.after(0, lambda: self.set_status(
                f"Buscando taxas históricas... ({completed}/{total} concluídas)"
            ))

        def _source_cb(source: str) -> None:
            self._data_source = source

        def worker() -> None:
            try:
                historical = self._client.fetch_historical_rates(
                    reference_date, source_callback=_source_cb,
                    progress_callback=progress,
                )
            except Exception as exc:
                try:
                    log_exception(
                        logger,
                        exc,
                        "Falha ao buscar dados históricos",
                    )
                finally:
                    self.root.after(
                        0,
                        lambda error=exc: self.handle_fetch_error(error),
                    )
                return
            self.root.after(0, lambda: self.handle_historical_fetch_success(historical))
        threading.Thread(target=worker, daemon=True).start()

    def handle_fetch_success(self: App, records: Data) -> None:
        """Processa os registros carregados e atualiza a interface."""
        self.records = list(records)
        self._redraw_chart()
        self._update_button_states()
        self.settings["last_date"] = self.date_var.get().strip()
        record_reference(self.settings, self._last_reference_date, bool(records))
        self._update_stats()
        if self.evolution_var.get() and not self.historical_data and records:
            self._fetch_historical_rates(self._last_reference_date)
            return
        self._set_ui_locked(False)
        now = datetime.now(UTC).strftime("%H:%M:%S")
        if records:
            self.set_status(
                f"{len(records)} registro(s) carregado(s)  |  {self._data_source}  |  {now}",
                msg_type="success")
        else:
            self.set_status("Nenhum registro encontrado para a data informada.")

    def handle_historical_fetch_success(self: App, historical: Data) -> None:
        """Processa os dados históricos carregados e atualiza a interface."""
        self._historical_fetching = False
        self._set_ui_locked(False)
        self.historical_data = historical
        self.records = list(historical.get(
            max(historical.keys()), []
        )) if historical else []
        self._redraw_chart()
        self._update_button_states()
        self.settings["last_date"] = self.date_var.get().strip()
        record_reference(
            self.settings,
            self._last_reference_date,
            bool(historical and any(historical.values())),
        )
        now = datetime.now(UTC).strftime("%H:%M:%S")
        message, msg_type = historical_status(
            historical, self._data_source, now
        )
        self.set_status(message, msg_type=msg_type)

    def handle_fetch_error(self: App, exc: Exception) -> None:
        """Trata erros de busca e exibe a mensagem na barra de status."""
        self._historical_fetching = False
        self._set_ui_locked(False)
        self.records = []
        self._redraw_chart()
        self._update_button_states()
        self.set_status(f"Erro ao buscar dados: {exc}", msg_type="error")
