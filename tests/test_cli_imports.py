import ast
from pathlib import Path

CLI_PATH = Path("src/b3_selic_pre/presentation/cli.py")


def _module_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_cli_does_not_import_gui_at_module_level():
    imports = _module_imports(CLI_PATH)
    assert not any(
        name == "b3_selic_pre.presentation.gui"
        or name.startswith("b3_selic_pre.presentation.gui.")
        for name in imports
    )
    assert "tkinter" not in imports
    assert "matplotlib" not in imports


def test_cli_keeps_lazy_gui_wrapper():
    source = CLI_PATH.read_text(encoding="utf-8")
    assert "def launch_gui(" in source
    assert "from b3_selic_pre.presentation.gui import launch_gui" in source
