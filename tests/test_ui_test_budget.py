"""Orçamento de testes de UI não headless.

Testes que exigem display (Tk) são caros, dependentes de ambiente e não
validam regras de negócio. Este guard limita o número total desses testes e
obriga que todo teste em arquivo que importa Tk/GUI seja explicitamente
marcado com ``@pytest.mark.ui``.

Ao migrar um teste de UI para headless, reduza ``UI_TEST_BUDGET``. Nunca
aumente o orçamento sem aprovação explícita em revisão.
"""

import ast
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

UI_TEST_BUDGET = 5
UI_TEST_HARD_CAP = 5

UI_IMPORT_PREFIXES = (
    "tkinter",
    "b3_selic_pre.presentation.gui",
)


def _test_files() -> list[Path]:
    return sorted(TESTS_DIR.glob("test_*.py"))


def _has_ui_marker(decorators: list[ast.expr]) -> bool:
    for decorator in decorators:
        if not isinstance(decorator, ast.Attribute):
            continue
        if decorator.attr != "ui":
            continue
        value = decorator.value
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "mark"
            and isinstance(value.value, ast.Name)
            and value.value.id == "pytest"
        ):
            return True
    return False


def _is_test_function(node: ast.AST) -> bool:
    return isinstance(node, ast.FunctionDef) and node.name.startswith("test_")


def _iter_tests(tree: ast.Module):
    for node in tree.body:
        if _is_test_function(node):
            yield node, _has_ui_marker(node.decorator_list)
        elif isinstance(node, ast.ClassDef):
            class_is_ui = _has_ui_marker(node.decorator_list)
            for child in node.body:
                if _is_test_function(child):
                    yield child, class_is_ui or _has_ui_marker(
                        child.decorator_list
                    )


def _imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
        ):
            modules.add(node.module)
    return modules


def _uses_ui(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        module == prefix or module.startswith(prefix + ".")
        for module in _imported_modules(tree)
        for prefix in UI_IMPORT_PREFIXES
    )


def _ui_tests() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in _test_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node, is_ui in _iter_tests(tree):
            if is_ui:
                found.append((path, node.name))
    return found


def _unmarked_ui_file_tests() -> list[tuple[Path, str]]:
    unmarked: list[tuple[Path, str]] = []
    for path in _test_files():
        if not _uses_ui(path):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node, is_ui in _iter_tests(tree):
            if not is_ui:
                unmarked.append((path, node.name))
    return unmarked


def test_ui_test_count_does_not_exceed_budget():
    tests = _ui_tests()
    assert len(tests) <= UI_TEST_BUDGET, (
        f"Há {len(tests)} testes de UI, acima do orçamento de "
        f"{UI_TEST_BUDGET}.\n"
        "Prefira um teste headless; se o teste de UI for realmente "
        "necessário, reduza outro ou obtenha aprovação explícita para "
        "aumentar o orçamento.\n"
        f"Testes encontrados: {sorted(name for _, name in tests)}"
    )


def test_ui_budget_never_increases_above_hard_cap():
    assert UI_TEST_BUDGET <= UI_TEST_HARD_CAP, (
        "O orçamento de testes de UI não pode crescer. Reduza "
        "UI_TEST_BUDGET ao migrar testes para headless; aumente o hard cap "
        "somente com aprovação explícita em revisão."
    )


def test_tests_in_ui_files_are_marked_as_ui():
    unmarked = _unmarked_ui_file_tests()
    assert not unmarked, (
        "Todo teste em arquivo que importa Tk/GUI deve ser marcado com "
        "@pytest.mark.ui:\n"
        + "\n".join(f"  {path.name}::{name}" for path, name in unmarked)
    )
