import sys
import unittest
from pathlib import Path
from unittest import mock

from b3_selic_pre import __version__
from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.presentation.cli import main, parse_args


class ParseArgsHelpTest(unittest.TestCase):
    def test_description_in_help(self):
        with mock.patch("argparse.ArgumentParser") as mock_parser:
            mock_parser.return_value.parse_args.return_value = mock.Mock()
            parse_args(["2026-06-10"])
        init_call = mock_parser.call_args
        self.assertEqual(
            init_call.kwargs["description"],
            "Consulta taxas referenciais SELIC Pré na B3.",
        )

    def test_help_texts_present(self):
        calls = []
        original_add = __import__("argparse").ArgumentParser.add_argument

        class FakeParser:
            def __init__(self, **kwargs):
                self._calls = calls
                self.__class__._calls = calls

            def add_argument(self, *args, **kwargs):
                calls.append((args, kwargs))

            def add_mutually_exclusive_group(self):
                class G:
                    def add_argument(self, *a, **k):
                        calls.append((a, k))
                return G()

            def parse_args(self, argv):
                return mock.Mock()

        with mock.patch("argparse.ArgumentParser", FakeParser):
            parse_args(["2026-06-10"])
        helps = [k["help"] for _, k in calls]
        self.assertIn("Data de referência no formato YYYY-MM-DD.", helps)
        self.assertIn("Exibe taxas do dia corrente no terminal.", helps)
        self.assertIn("Abre a interface gráfica desktop.", helps)
        self.assertIn(
            "Exibe taxas consolidadas por ano (ANO, MENOR TAXA, MAIOR TAXA).",
            helps,
        )
        self.assertIn("Cria atalho no desktop e menu de aplicações e sai.", helps)
        self.assertIn("Ignora o cache em disco e baixa os dados da B3 novamente.", helps)
        self.assertIn("Exibe a versão do programa e sai.", helps)

    def test_shortcut_flag_help(self):
        calls = []

        class FakeParser:
            def __init__(self, **kwargs):
                pass

            def add_argument(self, *args, **kwargs):
                calls.append((args, kwargs))

            def add_mutually_exclusive_group(self):
                class G:
                    def add_argument(self, *a, **k):
                        calls.append((a, k))
                return G()

            def parse_args(self, argv):
                return mock.Mock()

        with mock.patch("argparse.ArgumentParser", FakeParser):
            parse_args([])
        shortcut = next(c for c in calls if "--create-shortcut" in c[0])
        self.assertEqual(shortcut[1]["help"], "Cria atalho no desktop e menu de aplicações e sai.")
        no_cache = next(c for c in calls if "--no-cache" in c[0])
        self.assertEqual(no_cache[1]["help"], "Ignora o cache em disco e baixa os dados da B3 novamente.")

    def test_version_action(self):
        calls = []

        class FakeParser:
            def __init__(self, **kwargs):
                pass

            def add_argument(self, *args, **kwargs):
                calls.append((args, kwargs))

            def add_mutually_exclusive_group(self):
                class G:
                    def add_argument(self, *a, **k):
                        calls.append((a, k))
                return G()

            def parse_args(self, argv):
                return mock.Mock()

        with mock.patch("argparse.ArgumentParser", FakeParser):
            parse_args([])
        version = next(c for c in calls if "--version" in c[0])
        self.assertEqual(version[1]["version"], f"b3-selic-pre {__import__('b3_selic_pre').__version__}")
        self.assertEqual(version[1]["help"], "Exibe a versão do programa e sai.")


class MainArgvTest(unittest.TestCase):
    def test_no_args_launches_gui(self):
        with mock.patch("b3_selic_pre.presentation.cli.launch_gui") as mock_gui:
            main([])
        mock_gui.assert_called_once()

    def test_none_argv_uses_sys_argv(self):
        with mock.patch("sys.argv", ["b3-selic-pre", "--gui"]), mock.patch(
            "b3_selic_pre.presentation.cli.launch_gui"
        ) as mock_gui:
            main(None)
        mock_gui.assert_called_once()

    def test_main_delegates_today_resolution_to_application(self):
        from b3_selic_pre.domain.models import RateRecord

        records = [RateRecord(day252=1, day360=1, rate="14.65")]
        with mock.patch(
            "b3_selic_pre.presentation.cli.configure_logging",
            return_value=None,
        ), mock.patch(
            "b3_selic_pre.presentation.cli.install_exception_hooks"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.logging.getLogger"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.resolve_reference_date",
            return_value="2026-06-10",
        ) as mock_resolve, mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as mock_cls:
            mock_client = mock.Mock()
            mock_client.fetch_reference_rates.return_value = records
            mock_cls.return_value = mock_client
            with mock.patch("b3_selic_pre.presentation.cli.print"):
                main(["--today"])
        mock_resolve.assert_called_once_with(None, use_today=True)
        mock_client.fetch_reference_rates.assert_called_once_with(
            "2026-06-10", force=False
        )

    def test_main_logs_startup_line(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.configure_logging",
            return_value=Path("/tmp/b3-selic-pre.log"),
        ), mock.patch(
            "b3_selic_pre.presentation.cli.install_exception_hooks"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.logging.getLogger"
        ) as mock_get_logger, mock.patch(
            "b3_selic_pre.presentation.cli.resolve_reference_date",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as mock_cls:
            mock_client = mock.Mock()
            mock_client.fetch_reference_rates.return_value = []
            mock_cls.return_value = mock_client
            with mock.patch("b3_selic_pre.presentation.cli.print"):
                main(["--today"])
        mock_get_logger.return_value.info.assert_called_once_with(
            "Iniciando b3-selic-pre %s (CLI); log em %s",
            __version__,
            Path("/tmp/b3-selic-pre.log"),
        )

    def test_main_communication_error_exits_with_code_one(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.configure_logging",
            return_value=None,
        ), mock.patch(
            "b3_selic_pre.presentation.cli.install_exception_hooks"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.logging.getLogger"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.resolve_reference_date",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as mock_cls, mock.patch(
            "b3_selic_pre.presentation.cli.log_exception"
        ) as mock_log, mock.patch(
            "b3_selic_pre.presentation.cli.print"
        ) as mock_print:
            mock_cls.return_value.fetch_reference_rates.side_effect = (
                CommunicationError("offline")
            )
            with self.assertRaises(SystemExit) as context:
                main(["--today"])
        self.assertEqual(context.exception.code, 1)
        self.assertIsInstance(mock_log.call_args.args[1], CommunicationError)
        self.assertEqual(mock_log.call_args.args[2], "Erro ao buscar dados")
        mock_print.assert_called_once_with(
            "Erro ao buscar dados: offline", file=sys.stderr
        )

    def test_main_non_communication_error_is_reraised(self):
        with mock.patch(
            "b3_selic_pre.presentation.cli.configure_logging",
            return_value=None,
        ), mock.patch(
            "b3_selic_pre.presentation.cli.install_exception_hooks"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.logging.getLogger"
        ), mock.patch(
            "b3_selic_pre.presentation.cli.resolve_reference_date",
            return_value="2026-06-10",
        ), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as mock_cls, mock.patch(
            "b3_selic_pre.presentation.cli.log_exception"
        ) as mock_log, mock.patch(
            "b3_selic_pre.presentation.cli.print"
        ):
            mock_cls.return_value.fetch_reference_rates.side_effect = ValueError(
                "bad"
            )
            with self.assertRaises(ValueError):
                main(["--today"])
        self.assertIsInstance(mock_log.call_args.args[1], ValueError)


if __name__ == "__main__":
    unittest.main()
