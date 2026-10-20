import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from b3_selic_pre import __version__
from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.use_cases import (
    FutureQueryDateError,
    OldQueryDateError,
)
from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.presentation import cli, cli_data


def _records(*rates):
    return [
        RateRecord(
            day252=i + 1,
            day360=(i + 1) * 30,
            rate=str(rate).replace(".", ","),
        )
        for i, rate in enumerate(rates)
    ]


def _settings():
    settings = mock.Mock()
    settings.log_retention_days.return_value = 7
    settings.get.return_value = {}
    return settings


class CliTestBase(unittest.TestCase):
    def setUp(self):
        self.settings = _settings()
        self.settings_patch = mock.patch(
            "b3_selic_pre.presentation.cli.Settings",
            return_value=self.settings,
        )
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)
        self.configure_patch = mock.patch(
            "b3_selic_pre.presentation.cli.configure_logging",
            return_value=Path("/tmp/b3-selic-pre.log"),
        )
        self.configure_logging = self.configure_patch.start()
        self.addCleanup(self.configure_patch.stop)
        self.hooks_patch = mock.patch(
            "b3_selic_pre.presentation.cli.install_exception_hooks"
        )
        self.hooks_patch.start()
        self.addCleanup(self.hooks_patch.stop)
        self.log_invocation_patch = mock.patch(
            "b3_selic_pre.presentation.cli.log_invocation"
        )
        self.log_invocation = self.log_invocation_patch.start()
        self.addCleanup(self.log_invocation_patch.stop)
        self.log_exception_patch = mock.patch(
            "b3_selic_pre.presentation.cli.log_exception"
        )
        self.log_exception = self.log_exception_patch.start()
        self.addCleanup(self.log_exception_patch.stop)

    def _main(self, argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()


class ParserTest(CliTestBase):
    def test_help_lists_subcommands(self):
        code, output, _ = self._main(["--help"])

        self.assertEqual(code, 0)
        for command in ("consultar", "atualizar", "exportar", "gui", "criar-atalho"):
            self.assertIn(command, output)

    def test_version_prints_version(self):
        code, output, _ = self._main(["--version"])

        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), f"b3-selic-pre {__version__}")

    def test_legacy_positional_date_is_rejected(self):
        code, _, stderr = self._main(["2026-06-10"])

        self.assertEqual(code, 2)
        self.assertIn("invalid choice", stderr)
        self.assertEqual(self.log_invocation.call_args.args[6], 2)

    def test_legacy_flags_are_rejected(self):
        for flag in ("--gui", "--today", "--yearly", "--create-shortcut"):
            with self.subTest(flag=flag):
                code, _, stderr = self._main([flag])
                self.assertEqual(code, 2)
                self.assertIn("unrecognized arguments", stderr)

    def test_parse_args_defaults(self):
        consultar = cli.parse_args(["consultar"])
        self.assertEqual(consultar.comando, "consultar")
        self.assertEqual(consultar.curva, "curta")
        self.assertIsNone(consultar.data)
        self.assertFalse(consultar.no_cache)

        atualizar = cli.parse_args(["atualizar"])
        self.assertFalse(atualizar.silencioso)

        exportar = cli.parse_args(["exportar", "--curva", "ambas"])
        self.assertEqual(exportar.curva, "ambas")
        self.assertFalse(exportar.analise)
        self.assertFalse(exportar.log)
        self.assertIsNone(exportar.saida)


class DataResolutionTest(CliTestBase):
    def _resolve(self, value):
        with mock.patch(
            "b3_selic_pre.presentation.cli_data.default_reference_date",
            return_value="2026-06-17",
        ), mock.patch(
            "b3_selic_pre.application.use_cases.default_reference_date",
            return_value="2026-06-17",
        ):
            return cli_data.resolve_data(value)

    def test_default_uses_today(self):
        self.assertEqual(self._resolve(None), "2026-06-17")

    def test_weekend_retreats_to_friday(self):
        self.assertEqual(self._resolve("2026-06-14"), "2026-06-12")

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            self._resolve("14/06/2026")

    def test_future_date_is_rejected(self):
        with self.assertRaises(FutureQueryDateError):
            self._resolve("2026-06-18")

    def test_old_date_is_rejected(self):
        with self.assertRaises(OldQueryDateError):
            self._resolve("2026-05-01")

    def test_invalid_data_returns_two_without_client(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            code, _, stderr = self._main(["consultar", "--data", "invalida"])

        self.assertEqual(code, 2)
        self.assertIn("YYYY-MM-DD", stderr)
        client_class.return_value.fetch_rates_for_date.assert_not_called()
        self.assertEqual(self.log_invocation.call_args.args[6], 2)


class ConsultarTest(CliTestBase):
    def _run_consultar(self, *extra, records=None, side_effect=None):
        with mock.patch(
            "b3_selic_pre.presentation.cli_commands.resolve_data",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            client = client_class.return_value
            if side_effect is None:
                client.fetch_rates_for_date.return_value = (
                    records if records is not None else _records(14.5, 15.0)
                )
            else:
                client.fetch_rates_for_date.side_effect = side_effect
            result = self._main(["consultar", "--data", "2026-06-10", *extra])
        return result, client

    def test_curta_outputs_raw_csv(self):
        (code, output, _), client = self._run_consultar()

        self.assertEqual(code, 0)
        self.assertTrue(output.startswith("DU252,DC365,TAXA\n"))
        client.fetch_rates_for_date.assert_called_once_with(
            "2026-06-10", force=False
        )

    def test_longa_outputs_consolidated_csv(self):
        (code, output, _), _ = self._run_consultar("--curva", "longa")

        self.assertEqual(code, 0)
        self.assertTrue(output.startswith("ANO,MENOR_TAXA,MAIOR_TAXA\n"))

    def test_ambas_outputs_both_sections(self):
        (code, output, _), _ = self._run_consultar("--curva", "ambas")

        self.assertEqual(code, 0)
        self.assertIn("Curva curta", output)
        self.assertIn("Curva longa", output)
        self.assertIn("DU252,DC365,TAXA", output)
        self.assertIn("ANO,MENOR_TAXA,MAIOR_TAXA", output)

    def test_no_cache_forces_fetch(self):
        (code, _, _), client = self._run_consultar("--no-cache")

        self.assertEqual(code, 0)
        client.fetch_rates_for_date.assert_called_once_with(
            "2026-06-10", force=True
        )

    def test_empty_records_return_one(self):
        (code, _, stderr), _ = self._run_consultar(records=[])

        self.assertEqual(code, 1)
        self.assertIn("Nenhum registro encontrado", stderr)

    def test_communication_error_returns_one(self):
        (code, _, stderr), _ = self._run_consultar(
            side_effect=CommunicationError("offline")
        )

        self.assertEqual(code, 1)
        self.assertIn("Erro ao buscar dados: offline", stderr)
        self.log_exception.assert_called_once()
        self.assertEqual(self.log_invocation.call_args.args[6], 1)


class AtualizarTest(CliTestBase):
    def _historical(self, empty_date=None):
        dates = [
            "2026-05-20",
            "2026-05-27",
            "2026-06-03",
            "2026-06-10",
            "2026-06-17",
        ]
        return {
            date: ([] if date == empty_date else _records(14.5, 15.0))
            for date in dates
        }

    def _run_atualizar(self, *extra, historical=None, records=None):
        with mock.patch(
            "b3_selic_pre.presentation.cli_commands.resolve_data",
            return_value="2026-06-17",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            client = client_class.return_value
            client.fetch_rates_for_date.return_value = (
                records if records is not None else _records(14.5, 15.0)
            )
            client.fetch_historical_rates.return_value = (
                historical if historical is not None else self._historical()
            )
            result = self._main(["atualizar", "--data", "2026-06-17", *extra])
        return result, client

    def test_atualizar_prints_analysis_and_evolution(self):
        (code, output, _), client = self._run_atualizar()

        self.assertEqual(code, 0)
        self.assertIn("Análise da Curva", output)
        self.assertIn("Evolução da Curva", output)
        client.fetch_historical_rates.assert_called_once_with(
            "2026-06-17", force=False
        )

    def test_atualizar_silencioso_does_not_print(self):
        (code, output, _), _ = self._run_atualizar("--silencioso")

        self.assertEqual(code, 0)
        self.assertEqual(output, "")

    def test_atualizar_reports_missing_date(self):
        historical = self._historical(empty_date="2026-05-27")
        (code, output, _), _ = self._run_atualizar(historical=historical)

        self.assertEqual(code, 0)
        self.assertIn("Datas indisponíveis: 2026-05-27", output)

    def test_atualizar_without_base_records_returns_one(self):
        (code, _, stderr), _ = self._run_atualizar(
            historical={}, records=[]
        )

        self.assertEqual(code, 1)
        self.assertIn("Nenhum registro encontrado", stderr)


class ExportarTest(CliTestBase):
    def _historical(self):
        return {
            "2026-06-10": _records(14.4, 14.9),
            "2026-06-17": _records(14.5, 15.0),
        }

    def _run_exportar(self, *extra, historical=None):
        with mock.patch(
            "b3_selic_pre.presentation.cli_commands.resolve_data",
            return_value="2026-06-17",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            client = client_class.return_value
            client.fetch_historical_rates.return_value = (
                historical if historical is not None else self._historical()
            )
            result = self._main(["exportar", "--data", "2026-06-17", *extra])
        return result, client

    def test_one_artifact_goes_to_stdout(self):
        (code, output, _), _ = self._run_exportar("--curva", "longa")

        self.assertEqual(code, 0)
        self.assertTrue(output.startswith("DATA;ANO;TAXA_MEDIA\n"))

    def test_multiple_artifacts_are_written_to_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (code, output, _), _ = self._run_exportar(
                "--curva", "ambas", "--analise", "--saida", tmpdir
            )

            self.assertEqual(code, 0)
            self.assertEqual(output, "")
            names = {path.name for path in Path(tmpdir).iterdir()}
        self.assertEqual(
            names, {"curva-curta.csv", "curva-longa.csv", "analise.txt"}
        )

    def test_multiple_artifacts_require_directory(self):
        (code, _, stderr), _ = self._run_exportar(
            "--curva", "ambas", "--analise"
        )

        self.assertEqual(code, 2)
        self.assertIn("--saida", stderr)

    def test_saida_file_with_multiple_artifacts_returns_two(self):
        with tempfile.NamedTemporaryFile() as handle:
            (code, _, stderr), _ = self._run_exportar(
                "--curva", "ambas", "--analise", "--saida", handle.name
            )

        self.assertEqual(code, 2)
        self.assertIn("diretório", stderr)

    def test_no_content_returns_two(self):
        (code, _, stderr), _ = self._run_exportar()

        self.assertEqual(code, 2)
        self.assertIn("ao menos um conteúdo", stderr)

    def test_log_only_does_not_fetch_data(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli._log_text",
            return_value="log line\n",
        ):
            (code, output, _), client = self._run_exportar("--log")

        self.assertEqual(code, 0)
        self.assertEqual(output, "log line\n")
        client.fetch_historical_rates.assert_not_called()

    def test_selected_content_without_data_returns_one(self):
        (code, _, stderr), _ = self._run_exportar(
            "--curva", "curta", historical={}
        )

        self.assertEqual(code, 1)
        self.assertIn("Nenhum conteúdo disponível", stderr)


class GuiShortcutTest(CliTestBase):
    def test_no_args_launches_gui(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.launch_gui"
        ) as launch:
            code, _, _ = self._main([])

        self.assertEqual(code, 0)
        launch.assert_called_once_with(
            settings=self.settings,
            active_log=Path("/tmp/b3-selic-pre.log"),
            configure=False,
        )
        self.assertEqual(self.log_invocation.call_args.args[1], "gui")
        self.assertEqual(self.log_invocation.call_args.args[6], 0)

    def test_gui_subcommand_launches_gui(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.launch_gui"
        ) as launch:
            code, _, _ = self._main(["gui"])

        self.assertEqual(code, 0)
        launch.assert_called_once_with(
            settings=self.settings,
            active_log=Path("/tmp/b3-selic-pre.log"),
            configure=False,
        )

    def test_criar_atalho_calls_shortcut(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.create_shortcut"
        ) as create:
            code, output, _ = self._main(["criar-atalho"])

        self.assertEqual(code, 0)
        create.assert_called_once_with()
        self.assertIn("Atalho criado", output)

    def test_desktop_file_uses_gui_subcommand(self):
        content = Path("b3-selic-pre.desktop").read_text(encoding="utf-8")

        self.assertIn("Exec=b3-selic-pre gui", content)


class InvocationLogTest(CliTestBase):
    def _run_consultar(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli_commands.resolve_data",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            client_class.return_value.fetch_rates_for_date.return_value = (
                _records(14.5)
            )
            return self._main(
                ["consultar", "--data", "2026-06-10", "--curva", "longa"]
            )

    def test_success_logs_command_arguments_and_code(self):
        code, _, _ = self._run_consultar()

        self.assertEqual(code, 0)
        args = self.log_invocation.call_args.args
        self.assertEqual(args[1], "consultar")
        self.assertIn("data=2026-06-10", args[2])
        self.assertIn("curva=longa", args[2])
        self.assertIsInstance(args[5], float)
        self.assertEqual(args[6], 0)

    def test_help_is_logged_with_success(self):
        code, _, _ = self._main(["--help"])

        self.assertEqual(code, 0)
        self.assertEqual(self.log_invocation.call_args.args[1], "help")
        self.assertEqual(self.log_invocation.call_args.args[6], 0)

    def test_parse_error_is_logged(self):
        code, _, _ = self._main(["--gui"])

        self.assertEqual(code, 2)
        self.assertEqual(self.log_invocation.call_args.args[1], "desconhecido")
        self.assertIn("--gui", self.log_invocation.call_args.args[2])
        self.assertEqual(self.log_invocation.call_args.args[6], 2)

    def test_unhandled_exception_is_logged(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli_commands.resolve_data",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as client_class:
            client_class.return_value.fetch_rates_for_date.side_effect = (
                ValueError("bad")
            )
            with self.assertRaises(ValueError):
                self._main(["consultar", "--data", "2026-06-10"])

        self.assertEqual(self.log_invocation.call_args.args[6], 1)
        self.log_exception.assert_called_once()

    def test_cli_uses_settings_retention(self):
        self._run_consultar()

        self.configure_logging.assert_called_once_with(retention_days=7)


class GuiLaunchLoggingTest(unittest.TestCase):
    def test_launch_gui_does_not_reconfigure_logging(self):
        settings = _settings()
        with mock.patch(
            "b3_selic_pre.presentation.gui.launch.configure_logging"
        ) as configure, mock.patch(
            "b3_selic_pre.presentation.gui.launch.SelicPreApp"
        ) as app_class, mock.patch(
            "b3_selic_pre.presentation.gui.launch.GuiDependencies"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.CachedB3Client"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.install_tk_exception_hook"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch._icon_source",
            return_value="/tmp/icon.png",
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.shortcut_exists",
            return_value=False,
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.create_shortcut"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.open_url"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.open_directory"
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.fetch_latest_version",
            return_value=None,
        ), mock.patch(
            "b3_selic_pre.presentation.gui.launch.log_dir",
            return_value=Path("/tmp/logs"),
        ), mock.patch("tkinter.Tk") as tk_class:
            root = tk_class.return_value
            app_class.return_value = mock.Mock()
            cli.launch_gui(
                settings=settings,
                active_log=Path("/tmp/b3-selic-pre.log"),
                configure=False,
            )

        configure.assert_not_called()
        root.mainloop.assert_called_once()
