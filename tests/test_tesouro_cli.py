import argparse
import json
from decimal import Decimal
from unittest import mock

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.models import VendaTesouroDireto
from b3_selic_pre.presentation import cli, cli_commands


def _sales():
    return [
        VendaTesouroDireto(
            "Tesouro Selic 2029",
            "2029-01-02",
            "2026-10-01",
            Decimal("15000"),
            Decimal("2"),
            Decimal("30000"),
        ),
        VendaTesouroDireto(
            "Tesouro IPCA+ 2035",
            "2035-05-15",
            "2026-10-02",
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
    def __init__(self, sales=None, error=None):
        self.sales = _sales() if sales is None else sales
        self.error = error
        self.calls = []

    def fetch_vendas(self, force=False, source_callback=None):
        self.calls.append(force)
        if self.error is not None:
            raise self.error
        return self.sales, _metadata(), "cache"


def _args(**overrides):
    data = {
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


def _run(args, client, capsys):
    code = cli_commands.tesouro(args, client)
    output = capsys.readouterr()
    return code, output.out, output.err


class TestTesouroCommand:
    def test_default_csv(self, capsys):
        client = FakeClient()
        code, out, err = _run(_args(), client, capsys)

        assert code == 0
        assert err == ""
        assert out.startswith(
            "TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR\n"
        )
        assert client.calls == [False]

    def test_json_payload(self, capsys):
        code, out, _ = _run(_args(json=True), FakeClient(), capsys)
        payload = json.loads(out)

        assert code == 0
        assert payload["dataset"] == "vendas-do-tesouro-direto"
        assert payload["registros"][0]["pu"] == "3000.000000"
        assert payload["total_registros"] == 2

    def test_aggregated_csv_and_json(self, capsys):
        code, out, _ = _run(
            _args(agregar=True, titulo="selic"), FakeClient(), capsys
        )
        assert code == 0
        assert out.startswith("TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO\n")

        code, out, _ = _run(
            _args(agregar=True, json=True), FakeClient(), capsys
        )
        payload = json.loads(out)
        assert code == 0
        assert payload["total_agregados"] == 2
        assert "registros" not in payload

    def test_filter_by_title_and_period(self, capsys):
        code, out, _ = _run(
            _args(
                titulo="ipca",
                inicio="2026-10-02",
                fim="2026-10-02",
            ),
            FakeClient(),
            capsys,
        )

        assert code == 0
        assert "IPCA" in out
        assert "Selic" not in out

    def test_default_period_uses_newest_date(self, capsys):
        code, out, _ = _run(_args(inicio="2026-10-02"), FakeClient(), capsys)

        assert code == 0
        assert "IPCA" in out
        assert "Selic" not in out

    def test_empty_result_keeps_header(self, capsys):
        code, out, _ = _run(
            _args(inicio="2025-01-01", fim="2025-01-02"), FakeClient(), capsys
        )

        assert code == 0
        assert out.count("\n") == 1

    def test_no_cache_forces_fetch(self, capsys):
        client = FakeClient()
        _run(_args(no_cache=True), client, capsys)

        assert client.calls == [True]

    @pytest.mark.parametrize(
        "args",
        [
            {"inicio": "2026-10-02", "fim": "2026-10-01"},
            {"inicio": "02/10/2026"},
        ],
    )
    def test_invalid_period_returns_two_without_fetch(self, args, capsys):
        client = FakeClient()
        code, _, err = _run(_args(**args), client, capsys)

        assert code == 2
        assert "AAAA-MM-DD" in err or "--inicio" in err
        assert client.calls == []

    def test_communication_error_returns_one(self, capsys):
        code, _, err = _run(
            _args(), FakeClient(error=CommunicationError("offline")), capsys
        )

        assert code == 1
        assert "offline" in err

    def test_data_error_returns_one(self, capsys):
        code, _, err = _run(
            _args(), FakeClient(error=TesouroDataError("csv ruim")), capsys
        )

        assert code == 1
        assert "csv ruim" in err

    def test_saida_file(self, tmp_path, capsys):
        target = tmp_path / "out.csv"
        code, out, _ = _run(_args(saida=str(target)), FakeClient(), capsys)

        assert code == 0
        assert out == ""
        assert target.read_text(encoding="utf-8").startswith("TIPO_TITULO;")

    def test_saida_directory_uses_aggregated_name(self, tmp_path, capsys):
        code, out, _ = _run(
            _args(agregar=True, json=True, saida=str(tmp_path)),
            FakeClient(),
            capsys,
        )

        assert code == 0
        assert out == ""
        assert (tmp_path / "tesouro-vendas-agregado.json").exists()

    def test_saida_write_failure_returns_one(self, tmp_path, capsys):
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")
        code, _, err = _run(
            _args(saida=str(blocker / "out.csv")), FakeClient(), capsys
        )

        assert code == 1
        assert "Falha ao gravar" in err


class TestTesouroParserAndDispatch:
    def test_parser_defaults(self):
        args = cli.parse_args(["tesouro"])

        assert args.comando == "tesouro"
        assert args.titulo is None
        assert args.inicio is None
        assert args.fim is None
        assert args.agregar is False
        assert args.json is False
        assert args.no_cache is False
        assert args.saida is None

    def test_dispatch_uses_dedicated_lock_and_client(self):
        lock = mock.MagicMock()
        lock.__enter__.return_value = lock
        lock.__exit__.return_value = None
        with mock.patch(
            "b3_selic_pre.presentation.cli.ActionLock", return_value=lock
        ) as lock_class, mock.patch(
            "b3_selic_pre.presentation.cli.TesouroDiretoClient"
        ) as client_class, mock.patch(
            "b3_selic_pre.presentation.cli.cli_commands.tesouro",
            return_value=0,
        ) as handler:
            code = cli._dispatch(
                argparse.Namespace(comando="tesouro"), mock.MagicMock(), None
            )

        assert code == 0
        assert lock_class.call_args.kwargs["path"].name == "tesouro.lock"
        handler.assert_called_once_with(
            mock.ANY, client_class.return_value
        )
