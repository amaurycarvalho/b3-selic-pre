import unittest
from unittest import mock

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

    def test_main_uses_utc_today(self):
        import b3_selic_pre.presentation.cli as cli
        real_datetime = cli.datetime
        calls = []

        class _FakeDatetime:
            @staticmethod
            def now(tz=None):
                calls.append(tz)
                return real_datetime.now(tz)

        records = [__import__("b3_selic_pre.domain.models", fromlist=["RateRecord"]).RateRecord(day252=1, day360=1, rate="14.65")]
        with mock.patch.object(cli, "datetime", _FakeDatetime), mock.patch(
            "b3_selic_pre.presentation.cli.CachedB3Client"
        ) as mock_cls:
            mock_client = mock.Mock()
            mock_client.fetch_reference_rates.return_value = records
            mock_cls.return_value = mock_client
            with mock.patch("b3_selic_pre.presentation.cli.print"):
                main(["--today"])
        self.assertIn(__import__("datetime").timezone.utc, calls)


if __name__ == "__main__":
    unittest.main()
