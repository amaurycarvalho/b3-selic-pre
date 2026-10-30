import argparse
import json
from decimal import Decimal

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
)
from b3_selic_pre.presentation import cli_commands, cli_parser


def _resgates():
    return [
        ResgateTesouroDireto(
            "recompra",
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-10-01",
            None,
            Decimal("2"),
            Decimal("30000"),
        ),
        ResgateTesouroDireto(
            "cupom",
            "Tesouro IPCA+ 2035",
            "2035-05-15",
            "2026-10-02",
            Decimal("3000"),
            Decimal("1"),
            Decimal("3000"),
        ),
        ResgateTesouroDireto(
            "recompra",
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-10-01",
            None,
            Decimal("3"),
            Decimal("42000"),
        ),
    ]


def _estoque():
    return [
        EstoqueTesouroDireto(
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-09",
            Decimal("15000"),
            Decimal("2"),
            Decimal("30000"),
        ),
        EstoqueTesouroDireto(
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-09",
            Decimal("14000"),
            Decimal("3"),
            Decimal("42000"),
        ),
        EstoqueTesouroDireto(
            "Tesouro IPCA+ 2035",
            "2035-05-15",
            "2026-08",
            Decimal("3000"),
            Decimal("1"),
            Decimal("3000"),
        ),
    ]


def _metadata():
    return {
        "resource_id": "resource-id",
        "checked_at": "2026-10-20T00:00:00+00:00",
        "last_modified": "2026-10-16T10:29:05",
        "last_data_date": "2026-10-02",
    }


class FakeClient:
    def __init__(self, records=None, error=None, resource="resgates"):
        self.records = records
        self.error = error
        self.resource = resource
        self.calls = []

    def fetch_resgates(self, force=False, source_callback=None):
        self.calls.append(force)
        if self.error is not None:
            raise self.error
        return self.records or [], _metadata(), "cache"

    def fetch_estoque(self, force=False, source_callback=None):
        return self.fetch_resgates(force, source_callback)


def _args(**overrides):
    data = {
        "tipo": None,
        "titulo": None,
        "inicio": None,
        "fim": None,
        "agregar": False,
        "json": False,
        "no_cache": False,
        "saida": None,
    }
    data.update(overrides)
    return argparse.Namespace(**data)


def _estoque_args(**overrides):
    data = {
        "titulo": None,
        "inicio": None,
        "fim": None,
        "mes": None,
        "agregar": False,
        "json": False,
        "no_cache": False,
        "saida": None,
    }
    data.update(overrides)
    return argparse.Namespace(**data)


def _run(handler, args, client, capsys):
    code = handler(args, client)
    output = capsys.readouterr()
    return code, output.out, output.err


class TestResgatesCommand:
    def test_default_csv(self, capsys):
        code, out, err = _run(
            cli_commands.tesouro_resgates,
            _args(),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert out.splitlines()[0] == (
            "TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;"
            "PU;QUANTIDADE;VALOR"
        )
        assert "recompra" in out
        assert err == ""

    def test_filter_by_tipo_and_titulo(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(tipo="cupom", titulo="ipca"),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert "recompra" not in out
        assert "cupom;Tesouro IPCA+ 2035" in out

    def test_json_payload(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(json=True),
            FakeClient(_resgates()),
            capsys,
        )
        payload = json.loads(out)
        assert code == 0
        assert payload["dataset"] == "resgates"
        assert payload["registros"][0]["tipo_resgate"] == "cupom"

    def test_aggregated_csv(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(agregar=True),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert out.splitlines()[0] == (
            "TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO"
        )
        assert "recompra;Tesouro Selic 2029;5.00;72000.00;" in out

    def test_aggregated_json(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(agregar=True, json=True),
            FakeClient(_resgates()),
            capsys,
        )
        payload = json.loads(out)
        assert code == 0
        assert "agregados" in payload
        assert "registros" not in payload

    def test_period_validation_prevents_download(self, capsys):
        client = FakeClient(_resgates())
        code, _out, err = _run(
            cli_commands.tesouro_resgates,
            _args(inicio="2026-10-02", fim="2026-10-01"),
            client,
            capsys,
        )
        assert code == 2
        assert client.calls == []
        assert "inicio" in err

    def test_invalid_date_prevents_download(self, capsys):
        client = FakeClient(_resgates())
        code, _out, _err = _run(
            cli_commands.tesouro_resgates,
            _args(inicio="2026-1"),
            client,
            capsys,
        )
        assert code == 2
        assert client.calls == []

    def test_empty_result_has_header(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(inicio="2030-01-01", fim="2030-01-02"),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert out.splitlines() == [
            "TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;"
            "PU;QUANTIDADE;VALOR"
        ]

    def test_json_empty_result(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(inicio="2030-01-01", fim="2030-01-02", json=True),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert json.loads(out)["registros"] == []

    def test_no_cache_is_forwarded(self, capsys):
        client = FakeClient(_resgates())
        _run(
            cli_commands.tesouro_resgates,
            _args(no_cache=True),
            client,
            capsys,
        )
        assert client.calls == [True]

    @pytest.mark.parametrize(
        "error", [CommunicationError("offline"), TesouroDataError("bad")]
    )
    def test_fetch_errors_return_one(self, error, capsys):
        code, out, err = _run(
            cli_commands.tesouro_resgates,
            _args(),
            FakeClient(error=error),
            capsys,
        )
        assert code == 1
        assert out == ""
        assert "Erro ao consultar o Tesouro" in err

    def test_saida_to_file(self, tmp_path, capsys):
        target = tmp_path / "resgates.csv"
        code, out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(saida=str(target)),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert out == ""
        assert target.read_text(encoding="utf-8").startswith(
            "TIPO_RESGATE;"
        )

    def test_saida_to_directory_and_aggregated_name(
        self, tmp_path, capsys
    ):
        target = tmp_path / "exports"
        target.mkdir()
        code, _out, _ = _run(
            cli_commands.tesouro_resgates,
            _args(agregar=True, json=True, saida=str(target)),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 0
        assert (target / "tesouro-resgates-agregado.json").exists()

    def test_write_failure_returns_one(self, tmp_path, capsys):
        blocker = tmp_path / "file"
        blocker.write_text("x", encoding="utf-8")
        code, _out, err = _run(
            cli_commands.tesouro_resgates,
            _args(saida=str(blocker / "sub" / "resgates.csv")),
            FakeClient(_resgates()),
            capsys,
        )
        assert code == 1
        assert "Falha ao gravar" in err


class TestEstoqueCommand:
    def test_default_last_month(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 0
        assert out.splitlines()[0] == (
            "TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE"
        )
        assert "2026-09" in out
        assert "2026-08" not in out

    def test_interval_and_title(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(inicio="2026-08", fim="2026-09"),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 0
        assert "2026-08" in out
        assert "2026-09" in out

        code, filtered, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(
                inicio="2026-08", fim="2026-09", titulo="selic"
            ),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 0
        assert "2026-08" not in filtered
        assert "IPCA" not in filtered

    def test_mes_selects_single_month(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(mes="2026-08", json=True),
            FakeClient(_estoque()),
            capsys,
        )
        payload = json.loads(out)
        assert code == 0
        assert {item["mes"] for item in payload["registros"]} == {"2026-08"}

    def test_aggregation_in_single_month(self, capsys):
        code, out, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(mes="2026-09", agregar=True),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 0
        assert out.splitlines()[0] == (
            "TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO"
        )

    def test_aggregation_over_multiple_months_returns_two(self, capsys):
        code, out, err = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(
                inicio="2026-08", fim="2026-09", agregar=True
            ),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 2
        assert out == ""
        assert "único mês" in err

    def test_invalid_month_prevents_download(self, capsys):
        client = FakeClient(_estoque())
        code, _out, _err = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(inicio="2026-13"),
            client,
            capsys,
        )
        assert code == 2
        assert client.calls == []

    def test_json_and_saida_names(self, tmp_path, capsys):
        target = tmp_path / "exports"
        target.mkdir()
        code, _out, _ = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(json=True, saida=str(target)),
            FakeClient(_estoque()),
            capsys,
        )
        assert code == 0
        payload = json.loads(
            (target / "tesouro-estoque.json").read_text(encoding="utf-8")
        )
        assert payload["dataset"] == "estoque"

    def test_fetch_error_returns_one(self, capsys):
        code, _out, err = _run(
            cli_commands.tesouro_estoque,
            _estoque_args(),
            FakeClient(error=CommunicationError("offline")),
            capsys,
        )
        assert code == 1
        assert "Erro ao consultar o Tesouro" in err


class TestParser:
    def test_new_subcommands_are_listed(self):
        parser = cli_parser.build_parser()
        help_text = parser.format_help()
        assert "tesouro-resgates" in help_text
        assert "tesouro-estoque" in help_text

    def test_resgates_options(self):
        args = cli_parser.parse_args(
            [
                "tesouro-resgates",
                "--tipo",
                "cupom",
                "--inicio",
                "2026-10-01",
                "--saida",
                "out.csv",
            ]
        )
        assert args.tipo == "cupom"
        assert args.inicio == "2026-10-01"
        assert args.saida == "out.csv"

    def test_estoque_options(self):
        args = cli_parser.parse_args(
            ["tesouro-estoque", "--mes", "2026-09", "--agregar"]
        )
        assert args.mes == "2026-09"
        assert args.agregar is True
