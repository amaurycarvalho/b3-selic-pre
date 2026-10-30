"""Testes do subcomando reservas da CLI."""

import json
from argparse import Namespace
from pathlib import Path

from b3_selic_pre.presentation import cli_commands, cli_parser


class FakeController:
    def __init__(self, payload=None, fail_refresh=False):
        self.payload = payload if payload is not None else _payload()
        self.load_calls = 0
        self.refresh_calls = 0
        self.force_calls = []
        self.fail_refresh = fail_refresh

    def load_cache_only(self):
        self.load_calls += 1
        return self.payload

    def refresh(self, force=False):
        self.refresh_calls += 1
        self.force_calls.append(force)
        if self.fail_refresh:
            raise OSError("rede")
        return self.payload


def _item(day, value):
    return {
        "data": day,
        "ativo": "reservas",
        "valor": value,
        "unidade": "USD_milhoes",
        "origem": "BCB SGS 13621",
        "metodo": "oficial",
        "extraido_em": "2026-10-30T12:00:00+00:00",
    }


def _payload():
    items = [
        _item("2024-01-01", 340000.0),
        _item("2025-01-01", 350000.0),
        _item("2026-10-30", 360000.0),
    ]
    serie = {
        "ativo": "reservas",
        "unidade": "USD_milhoes",
        "origem": "BCB SGS 13621",
        "itens": items,
    }
    return {
        "janela": {"inicio": "2024-01-01", "fim": "2026-10-30"},
        "serie": serie,
        "series": {"reservas": serie},
        "indicadores": {
            "nivel_atual": 360.0,
            "regime": "aumento",
            "limiares": {"var_aumento": 2.0},
        },
        "regime": "aumento",
        "limiares": {"var_aumento": 2.0},
        "origem": "Cache",
        "gerado_em": "2026-10-30T12:00:00",
        "latest_data_date": "2026-10-30",
    }


def _args(**overrides):
    values = {
        "inicio": None,
        "fim": None,
        "janela": "12m",
        "formato": "csv",
        "indicadores": False,
        "saida": None,
        "no_cache": False,
        "atualizar": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_parser_lists_reservas_defaults_and_help():
    parser = cli_parser.build_parser()
    args = parser.parse_args(["reservas"])

    assert args.comando == "reservas"
    assert args.janela == "12m"
    assert args.formato == "csv"
    assert "reservas" in parser.format_help()
    assert parser.parse_args(["reservas", "--janela", "3a"]).janela == "3a"


def test_invalid_dates_return_2_without_loading(capsys):
    controller = FakeController()

    code = cli_commands.reservas(_args(inicio="31/12/2026"), controller)

    assert code == 2
    assert "AAAA-MM-DD" in capsys.readouterr().err
    assert controller.load_calls == 0


def test_inicio_after_fim_returns_2(capsys):
    code = cli_commands.reservas(
        _args(inicio="2026-12-31", fim="2026-01-01"), FakeController()
    )

    assert code == 2
    assert "posterior" in capsys.readouterr().err


def test_no_network_by_default(capsys):
    controller = FakeController()

    code = cli_commands.reservas(_args(), controller)

    assert code == 0
    assert controller.load_calls == 1
    assert controller.refresh_calls == 0
    assert "DATA;VALOR;UNIDADE;ORIGEM;METODO" in capsys.readouterr().out


def test_atualizar_and_no_cache_refresh_and_force():
    controller = FakeController()

    assert cli_commands.reservas(_args(atualizar=True), controller) == 0
    assert cli_commands.reservas(_args(no_cache=True), controller) == 0

    assert controller.refresh_calls == 2
    assert controller.force_calls == [False, True]


def test_default_window_is_twelve_months(capsys):
    code = cli_commands.reservas(_args(), FakeController())

    output = capsys.readouterr().out
    assert code == 0
    assert "2026-10-30" in output
    assert "2025-01-01" not in output


def test_three_year_window_includes_older_points(capsys):
    code = cli_commands.reservas(_args(janela="3a"), FakeController())

    output = capsys.readouterr().out
    assert code == 0
    assert "2024-01-01" in output
    assert "2025-01-01" in output


def test_json_stdout_contains_indicators(capsys):
    code = cli_commands.reservas(
        _args(formato="json", indicadores=True), FakeController()
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["indicadores"]["regime"] == "aumento"
    assert payload["serie"]["itens"][0]["data"] == "2026-10-30"


def test_default_directory_names(tmp_path):
    controller = FakeController()

    assert (
        cli_commands.reservas(_args(saida=str(tmp_path)), controller)
        == 0
    )
    assert (tmp_path / "reservas-serie.csv").exists()
    assert (
        cli_commands.reservas(
            _args(saida=str(tmp_path), formato="json"), controller
        )
        == 0
    )
    assert (tmp_path / "reservas.json").exists()


def test_single_artifact_can_be_written_to_file(tmp_path):
    target = tmp_path / "reservas.csv"

    code = cli_commands.reservas(
        _args(saida=str(target)), FakeController()
    )

    assert code == 0
    assert target.exists()


def test_write_failure_returns_1(tmp_path, capsys, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("sem permissão")

    from b3_selic_pre.presentation import cli_reserves

    monkeypatch.setattr(cli_reserves, "write_artifacts", fail)
    code = cli_commands.reservas(
        _args(saida=str(tmp_path / "saida")), FakeController()
    )

    assert code == 1
    assert "Falha ao gravar" in capsys.readouterr().err


def test_no_data_returns_1_and_guides_update(capsys):
    payload = _payload()
    payload["serie"] = {**payload["serie"], "itens": []}
    payload["series"] = {"reservas": payload["serie"]}

    code = cli_commands.reservas(_args(), FakeController(payload))

    assert code == 1
    assert "--atualizar" in capsys.readouterr().err


def test_refresh_failure_returns_1(capsys):
    code = cli_commands.reservas(
        _args(atualizar=True), FakeController(fail_refresh=True)
    )

    assert code == 1
    assert "Falha ao consultar as reservas" in capsys.readouterr().err


def test_reserves_handler_is_wired_in_cli_root():
    source = Path("src/b3_selic_pre/presentation/cli.py").read_text(
        encoding="utf-8"
    )
    assert 'if args.comando == "reservas"' in source
    assert "_dispatch_reservas" in source
    assert "build_reserves_services" in source
