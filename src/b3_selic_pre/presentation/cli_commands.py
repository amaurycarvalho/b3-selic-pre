"""Implementação dos subcomandos de dados da CLI."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Protocol

from b3_selic_pre.application.cli_services import build_export_artifacts
from b3_selic_pre.application.market.export import (
    forecast_artifact_from_payload,
    history_artifact_from_payload,
    json_artifact_from_payload,
)
from b3_selic_pre.application.market.payloads import filter_payload_window
from b3_selic_pre.application.use_cases import build_rates_table
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation.cli_data import (
    config_from_settings,
    print_artifact,
    resolve_data,
    write_artifacts,
)
from b3_selic_pre.presentation.settings import Settings


class RatesClient(Protocol):
    """Contrato mínimo do cliente de taxas usado pelos comandos."""

    def fetch_rates_for_date(
        self: RatesClient, date_str: str, force: bool = False, **kwargs: object
    ) -> list[RateRecord]:
        """Busca as taxas de uma data."""

    def fetch_historical_rates(
        self: RatesClient, base_date: str, force: bool = False, **kwargs: object
    ) -> dict[str, list[RateRecord]]:
        """Busca a janela de evolução."""


def _print_curva(records: list[RateRecord], curva: str) -> None:
    if curva == "ambas":
        print("Curva curta")
        print(build_rates_table(records), end="")
        print("\nCurva longa")
        print(build_rates_table(records, yearly=True), end="")
        return
    print(
        build_rates_table(records, yearly=curva == "longa"),
        end="",
    )


def consultar(args: argparse.Namespace, client: RatesClient) -> int:
    """Consulta a curva de uma data e imprime a representação escolhida."""
    try:
        data = resolve_data(args.data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    records = client.fetch_rates_for_date(
        data, force=args.no_cache
    )
    if not records:
        print(f"Nenhum registro encontrado para {data}.", file=sys.stderr)
        return 1
    _print_curva(records, args.curva)
    return 0


def load_update(
    client: RatesClient,
    data: str,
    no_cache: bool = False,
    source_callback: object | None = None,
    progress_callback: object | None = None,
) -> tuple[list[RateRecord], dict[str, list[RateRecord]]]:
    """Carrega a curva e a janela de evolução reutilizando o cliente informado."""
    callbacks: dict[str, object] = {}
    if source_callback is not None:
        callbacks["source_callback"] = source_callback
    records = client.fetch_rates_for_date(
        data, force=no_cache, **callbacks
    )
    historical_callbacks = dict(callbacks)
    if progress_callback is not None:
        historical_callbacks["progress_callback"] = progress_callback
    historical = client.fetch_historical_rates(
        data,
        force=no_cache,
        **historical_callbacks,
    )
    return records or historical.get(data, []), historical


def _print_update(
    records: list[RateRecord],
    historical: dict[str, list[RateRecord]],
    settings: Settings,
) -> None:
    artifacts = build_export_artifacts(
        records,
        historical_data=historical,
        include_analise=True,
        config=config_from_settings(settings),
    )
    if artifacts:
        print_artifact(artifacts[0])
    missing = sorted(date for date, values in historical.items() if not values)
    if missing:
        print(f"\nDatas indisponíveis: {', '.join(missing)}")


def atualizar(args: argparse.Namespace, settings: Settings, client: RatesClient) -> int:
    """Carrega curva e evolução e imprime a análise determinística."""
    try:
        data = resolve_data(args.data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    records, historical = load_update(client, data, args.no_cache)
    if not records:
        print(f"Nenhum registro encontrado para {data}.", file=sys.stderr)
        return 1
    settings["data_referencia"] = data
    if args.silencioso:
        return 0
    _print_update(records, historical, settings)
    return 0


def _no_content(args: argparse.Namespace) -> bool:
    return args.curva is None and not args.analise and not args.log


def _fetch_export(
    client: RatesClient, args: argparse.Namespace, data: str
) -> tuple[dict[str, list[RateRecord]] | None, list[RateRecord]]:
    if args.curva is None and not args.analise:
        return None, []
    historical = client.fetch_historical_rates(
        data, force=args.no_cache
    )
    records = historical.get(data, [])
    if not records and historical:
        records = historical[max(historical)]
    return historical, records


def exportar(
    args: argparse.Namespace,
    settings: Settings,
    client: RatesClient,
    log_content: str | None,
) -> int:
    """Seleciona e grava os artefatos solicitados pelo usuário."""
    if _no_content(args):
        print(
            "Selecione ao menos um conteúdo para exportar.",
            file=sys.stderr,
        )
        return 2
    analise_curva = getattr(args, "analise_curva", None)
    if analise_curva is not None and not args.analise:
        print(
            "--analise-curva exige --analise.",
            file=sys.stderr,
        )
        return 2
    try:
        data = resolve_data(args.data)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    historical, records = _fetch_export(client, args, data)
    artifacts = build_export_artifacts(
        records,
        historical_data=historical,
        curva=args.curva,
        include_analise=args.analise,
        log_text=log_content,
        config=config_from_settings(settings),
        analise_curva=analise_curva or "curta",
    )
    if not artifacts:
        print(
            "Nenhum conteúdo disponível para exportação.",
            file=sys.stderr,
        )
        return 1
    return write_artifacts(artifacts, args.saida)


def tesouro(args: argparse.Namespace, client: object) -> int:
    """Delega a consulta de vendas ao handler headless do Tesouro."""
    from b3_selic_pre.presentation.cli_tesouro import tesouro as _tesouro

    return _tesouro(args, client)


def tesouro_resgates(args: argparse.Namespace, client: object) -> int:
    """Delega a consulta de resgates ao handler headless do Tesouro."""
    from b3_selic_pre.presentation.cli_tesouro_datasets import (
        tesouro_resgates as _handler,
    )

    return _handler(args, client)


def tesouro_estoque(args: argparse.Namespace, client: object) -> int:
    """Delega a consulta de estoque ao handler headless do Tesouro."""
    from b3_selic_pre.presentation.cli_tesouro_datasets import (
        tesouro_estoque as _handler,
    )

    return _handler(args, client)


def _market_date(value: str | None, name: str) -> tuple[str | None, int]:
    if value is None:
        return None, 0
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        print(
            f"{name} inválida: use o formato AAAA-MM-DD.",
            file=sys.stderr,
        )
        return None, 2
    if parsed.isoformat() != value:
        print(
            f"{name} inválida: use o formato AAAA-MM-DD.",
            file=sys.stderr,
        )
        return None, 2
    return value, 0


def _filter_market_payload(
    payload: dict[str, object],
    ativo: str,
    inicio: str | None,
    fim: str | None,
) -> dict[str, object] | None:
    return filter_payload_window(payload, ativo, inicio, fim)


def _market_artifacts(
    payload: dict[str, object], args: argparse.Namespace
) -> list[object]:
    if args.formato == "json":
        return [json_artifact_from_payload(payload)]
    artifacts = [history_artifact_from_payload(payload)]
    if args.prever:
        artifacts.append(forecast_artifact_from_payload(payload))
    return artifacts


def _market_window(
    args: argparse.Namespace,
) -> tuple[str | None, str | None, int]:
    inicio, code = _market_date(args.inicio, "--inicio")
    if code:
        return None, None, code
    fim, code = _market_date(args.fim, "--fim")
    if code:
        return None, None, code
    if inicio is not None and fim is not None and inicio > fim:
        print("--inicio não pode ser posterior a --fim.", file=sys.stderr)
        return None, None, 2
    return inicio, fim, 0


def _market_load(
    args: argparse.Namespace, controller: object
) -> tuple[dict[str, object] | None, int]:
    try:
        payload = (
            controller.refresh()  # type: ignore[attr-defined]
            if args.atualizar or args.no_cache
            else controller.load_cache_only()  # type: ignore[attr-defined]
        )
    except Exception as exc:
        print(f"Falha ao consultar o mercado: {exc}", file=sys.stderr)
        return None, 1
    return payload, 0


def _market_filtered(
    payload: dict[str, object], args: argparse.Namespace,
    inicio: str | None, fim: str | None,
) -> dict[str, object] | None:
    filtered = _filter_market_payload(payload, args.ativo, inicio, fim)
    if filtered is None:
        print(
            "Não há dados de mercado em cache para a janela solicitada. "
            "Use --atualizar para buscar as fontes.",
            file=sys.stderr,
        )
    return filtered


def _market_write(
    filtered: dict[str, object], args: argparse.Namespace
) -> int:
    try:
        return write_artifacts(_market_artifacts(filtered, args), args.saida)
    except OSError as exc:
        print(f"Falha ao gravar a saída: {exc}", file=sys.stderr)
        return 1


def mercado(args: argparse.Namespace, controller: object) -> int:
    """Consulta ou exporta séries de dólar e ouro."""
    inicio, fim, code = _market_window(args)
    if code:
        return code
    controller.options.resolucao = args.resolucao  # type: ignore[attr-defined]
    payload, code = _market_load(args, controller)
    if payload is None:
        return code
    filtered = _market_filtered(payload, args, inicio, fim)
    if filtered is None:
        return 1
    return _market_write(filtered, args)
