"""Testes do subcomando mercado da CLI."""

import json
from argparse import Namespace
from pathlib import Path

from b3_selic_pre.presentation import cli_commands, cli_parser
from b3_selic_pre.presentation.market_view_model import MarketOptions


class FakeController:
    def __init__(self, payload=None, fail_refresh=False):
        self.payload = payload or {"series": {}, "previsao": {}, "janela": {}}
        self.options = MarketOptions()
        self.load_calls = 0
        self.refresh_calls = 0
        self.fail_refresh = fail_refresh

    def load_cache_only(self):
        self.load_calls += 1
        return self.payload

    def refresh(self):
        self.refresh_calls += 1
        if self.fail_refresh:
            raise OSError("rede")
        return self.payload


def _payload():
    return {
        "janela": {"inicio": "2026-01-01", "fim": "2026-12-31"},
        "series": {
            "usd": {
                "ativo": "usd",
                "unidade": "BRL/USD",
                "itens": [
                    {
                        "data": "2026-01-01",
                        "ativo": "usd",
                        "valor": 5.0,
                        "unidade": "BRL/USD",
                        "origem": "BCB",
                        "metodo": "oficial",
                    }
                ],
            },
            "ouro": {
                "ativo": "ouro",
                "unidade": "BRL/g",
                "itens": [
                    {
                        "data": "2026-01-01",
                        "ativo": "ouro",
                        "valor": 300.0,
                        "unidade": "BRL/g",
                        "origem": "derivado",
                        "metodo": "derivado",
                    }
                ],
            },
        },
        "previsao": {
            "usd": {
                "cenario": "Cenário de mercado",
                "itens": [
                    {
                        "data": "2027-01-31",
                        "ativo": "usd",
                        "cenario": "Cenário de mercado",
                        "metodo": "cenario_mercado",
                        "centro": 5.5,
                        "bandas": [
                            {"nivel": 80, "inferior": 5.2, "superior": 5.8},
                            {"nivel": 95, "inferior": 5.0, "superior": 6.0},
                        ],
                    }
                ],
            },
            "ouro": {
                "cenario": "Projeção estatística",
                "itens": [
                    {
                        "data": "2027-01-31",
                        "ativo": "ouro",
                        "cenario": "Projeção estatística",
                        "metodo": "projecao_estatistica",
                        "centro": 320.0,
                        "bandas": [
                            {"nivel": 80, "inferior": 300.0, "superior": 340.0},
                            {"nivel": 95, "inferior": 280.0, "superior": 360.0},
                        ],
                    }
                ],
            },
        },
        "indicadores": {},
        "origem": "Cache",
        "gerado_em": "2026-12-31T00:00:00",
    }


def _args(**overrides):
    values = {
        "inicio": None,
        "fim": None,
        "ativo": "ambos",
        "resolucao": "auto",
        "prever": False,
        "formato": "csv",
        "saida": None,
        "no_cache": False,
        "atualizar": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_parser_lists_mercado_and_defaults():
    parser = cli_parser.build_parser()
    args = parser.parse_args(["mercado"])

    assert args.comando == "mercado"
    assert args.ativo == "ambos"
    assert args.resolucao == "auto"
    assert args.formato == "csv"
    assert "mercado" in parser.format_help()


def test_invalid_dates_return_2_without_loading(capsys):
    controller = FakeController(_payload())

    code = cli_commands.mercado(_args(inicio="31/12/2026"), controller)

    assert code == 2
    assert "AAAA-MM-DD" in capsys.readouterr().err
    assert controller.load_calls == 0


def test_inicio_after_fim_returns_2(capsys):
    code = cli_commands.mercado(
        _args(inicio="2026-12-31", fim="2026-01-01"), FakeController(_payload())
    )

    assert code == 2
    assert "posterior" in capsys.readouterr().err


def test_no_cache_by_default_does_not_refresh(capsys):
    controller = FakeController(_payload())

    code = cli_commands.mercado(_args(), controller)

    assert code == 0
    assert controller.load_calls == 1
    assert controller.refresh_calls == 0
    assert "DATA;ATIVO" in capsys.readouterr().out


def test_atualizar_and_no_cache_refresh():
    controller = FakeController(_payload())

    assert cli_commands.mercado(_args(atualizar=True), controller) == 0
    assert cli_commands.mercado(_args(no_cache=True), controller) == 0
    assert controller.refresh_calls == 2


def test_asset_filter_keeps_only_requested_series(capsys):
    code = cli_commands.mercado(_args(ativo="ouro"), FakeController(_payload()))

    output = capsys.readouterr().out
    assert code == 0
    assert "ouro" in output
    assert "usd" not in output


def test_window_filter_without_data_returns_1(capsys):
    code = cli_commands.mercado(
        _args(inicio="2030-01-01", fim="2030-12-31"),
        FakeController(_payload()),
    )

    assert code == 1
    assert "--atualizar" in capsys.readouterr().err


def test_refresh_failure_returns_1(capsys):
    code = cli_commands.mercado(
        _args(atualizar=True), FakeController(_payload(), fail_refresh=True)
    )

    assert code == 1
    assert "Falha ao consultar" in capsys.readouterr().err


def test_multiple_csv_artifacts_require_directory(capsys):
    code = cli_commands.mercado(_args(prever=True), FakeController(_payload()))

    assert code == 2
    assert "diretório" in capsys.readouterr().err


def test_prever_writes_two_default_files(tmp_path):
    code = cli_commands.mercado(
        _args(prever=True, saida=str(tmp_path)), FakeController(_payload())
    )

    assert code == 0
    assert (tmp_path / "mercado-historico.csv").exists()
    assert (tmp_path / "mercado-previsao.csv").exists()
    forecast = (tmp_path / "mercado-previsao.csv").read_text()
    assert "Cenário de mercado" in forecast
    assert "5.2" in forecast and ";6;cenario_mercado" in forecast


def test_json_stdout_contains_forecast_and_origin(capsys):
    code = cli_commands.mercado(
        _args(formato="json", prever=True), FakeController(_payload())
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["origem"] == "Cache"
    assert "usd" in payload["previsao"]


def test_single_artifact_can_be_written_to_file(tmp_path):
    target = tmp_path / "saida.csv"

    code = cli_commands.mercado(_args(saida=str(target)), FakeController(_payload()))

    assert code == 0
    assert target.exists()


def test_write_failure_returns_1(tmp_path, capsys, monkeypatch):
    target = tmp_path / "arquivo"
    target.write_text("x")

    def fail(*args, **kwargs):
        raise OSError("sem permissão")

    monkeypatch.setattr(cli_commands, "write_artifacts", fail)
    code = cli_commands.mercado(_args(saida=str(target)), FakeController(_payload()))

    assert code == 1
    assert "Falha ao gravar" in capsys.readouterr().err


def test_resolution_is_applied_to_controller():
    controller = FakeController(_payload())

    cli_commands.mercado(_args(resolucao="mes"), controller)

    assert controller.options.resolucao == "mes"


def test_market_handler_is_wired_in_cli_root():
    source = Path("src/b3_selic_pre/presentation/cli.py").read_text(
        encoding="utf-8"
    )
    assert 'if args.comando == "mercado"' in source
    assert "_dispatch_mercado" in source
    assert "build_market_services" in source
