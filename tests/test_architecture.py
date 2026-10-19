"""Testes de guarda para as fronteiras da Clean Architecture.

As regras verificam o grafo real de imports em ``src/`` sem importar os
módulos (o que evita depender de Tk, matplotlib ou rede). Novas violações
falham imediatamente; exceções legítimas precisam ser adicionadas em
``tests/architecture_allowlist.py`` com justificativa explícita.
"""

import ast
from pathlib import Path

from tests.architecture_allowlist import EXTERNAL_IMPORTS, LAYER_IMPORTS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src" / "b3_selic_pre"

LAYERS = frozenset({"domain", "application", "infrastructure", "presentation"})

ALLOWED_LAYER_IMPORTS: dict[str, frozenset[str]] = {
    "domain": frozenset({"domain"}),
    "application": frozenset({"domain", "application"}),
    "infrastructure": frozenset({"domain", "application", "infrastructure"}),
    "presentation": frozenset({"domain", "application", "presentation"}),
}

FORBIDDEN_EXTERNAL_IMPORTS: dict[str, frozenset[str]] = {
    "domain": frozenset(
        {
            "base64",
            "csv",
            "http",
            "json",
            "matplotlib",
            "os",
            "pathlib",
            "PIL",
            "pyxclip",
            "requests",
            "shutil",
            "socket",
            "sqlite3",
            "subprocess",
            "tkinter",
            "urllib",
        }
    ),
    "application": frozenset(
        {
            "http",
            "matplotlib",
            "PIL",
            "pyxclip",
            "requests",
            "shutil",
            "socket",
            "subprocess",
            "tkinter",
            "urllib",
        }
    ),
    "infrastructure": frozenset({"matplotlib", "PIL", "pyxclip", "tkinter"}),
}


def _python_files() -> list[Path]:
    return sorted(
        path
        for path in SRC.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(SRC).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(("b3_selic_pre", *parts))


def _layer_of(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) >= 2 and parts[1] in LAYERS:
        return parts[1]
    return None


def _imported_modules(tree: ast.AST) -> set[str]:
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


def _imported_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
        ):
            roots.add(node.module.split(".")[0])
    return roots


def _layer_violations() -> set[tuple[str, str]]:
    violations: set[tuple[str, str]] = set()
    for path in _python_files():
        importer = _module_name(path)
        own_layer = _layer_of(importer)
        if own_layer is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for imported in _imported_modules(tree):
            imported_layer = _layer_of(imported)
            if (
                imported_layer is not None
                and imported_layer not in ALLOWED_LAYER_IMPORTS[own_layer]
            ):
                violations.add((importer, imported_layer))
    return violations


def _external_violations() -> set[tuple[str, str]]:
    violations: set[tuple[str, str]] = set()
    for path in _python_files():
        importer = _module_name(path)
        own_layer = _layer_of(importer)
        if own_layer is None:
            continue
        forbidden = FORBIDDEN_EXTERNAL_IMPORTS.get(own_layer, frozenset())
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for root in _imported_roots(tree):
            if root in forbidden:
                violations.add((importer, root))
    return violations


def _format(violations: set[tuple[str, str]]) -> str:
    return "\n".join(
        f"  {importer} -> {imported}"
        for importer, imported in sorted(violations)
    )


class TestLayerBoundaries:
    def test_layer_dependencies_follow_clean_architecture(self):
        unapproved = _layer_violations() - set(LAYER_IMPORTS)
        assert not unapproved, (
            "Violação de fronteira de camada detectada:\n"
            f"{_format(unapproved)}\n"
            "Corrija a dependência ou registre uma aprovação explícita em "
            "tests/architecture_allowlist.py."
        )

    def test_allowlisted_layer_exceptions_are_still_needed(self):
        stale = set(LAYER_IMPORTS) - _layer_violations()
        assert not stale, (
            "Aprovações de camada obsoletas (a violação não existe mais):\n"
            f"{_format(stale)}\n"
            "Remova a entrada de tests/architecture_allowlist.py."
        )


class TestInternalLayerPurity:
    def test_domain_has_no_io_or_framework_imports(self):
        violations = {
            item
            for item in _external_violations()
            if _layer_of(item[0]) == "domain"
        }
        unapproved = violations - set(EXTERNAL_IMPORTS)
        assert not unapproved, (
            "A camada domain deve ser pura (sem I/O, frameworks ou UI):\n"
            f"{_format(unapproved)}\n"
            "Mova a responsabilidade para infrastructure/application ou "
            "registre uma aprovação explícita."
        )

    def test_application_has_no_ui_or_network_imports(self):
        violations = {
            item
            for item in _external_violations()
            if _layer_of(item[0]) == "application"
        }
        assert not violations, (
            "A camada application deve ser headless (sem UI ou rede):\n"
            f"{_format(violations)}\n"
            "Injete a dependência a partir da presentation/infrastructure."
        )

    def test_infrastructure_has_no_ui_imports(self):
        violations = {
            item
            for item in _external_violations()
            if _layer_of(item[0]) == "infrastructure"
        }
        assert not violations, (
            "A camada infrastructure não deve depender de UI:\n"
            f"{_format(violations)}"
        )

    def test_allowlisted_external_exceptions_are_still_needed(self):
        stale = set(EXTERNAL_IMPORTS) - _external_violations()
        assert not stale, (
            "Aprovações externas obsoletas (a violação não existe mais):\n"
            f"{_format(stale)}\n"
            "Remova a entrada de tests/architecture_allowlist.py."
        )
