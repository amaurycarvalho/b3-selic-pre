## ADDED Requirements

### Requirement: Project uses src/ layout with Clean Architecture layers

The project SHALL be organized as a Python package under `src/b3_selic_pre/` with four layers: `domain/`, `application/`, `infrastructure/`, `presentation/`. Each layer SHALL be a sub-package with `__init__.py`.

#### Scenario: Package is discoverable by Python

- **WHEN** the package is installed via `pip install -e .`
- **THEN** `python -c "import b3_selic_pre; print(b3_selic_pre.__version__)"` SHALL output the current version

#### Scenario: All original functions remain accessible

- **WHEN** each public function from the original `b3_selic_pre.py` is called via its new module path
- **THEN** it SHALL produce the same output as before for identical input

### Requirement: Build is unified in pyproject.toml

The project SHALL have a `pyproject.toml` at the repository root containing `[build-system]`, `[project]`, `[project.scripts]`, `[tool.setuptools.packages.find]`, and `[tool.setuptools.package-data]` sections. The `requirements.txt` file SHALL be removed.

#### Scenario: pip install reads dependencies from pyproject.toml

- **WHEN** running `pip install .` or `pip install -e .` in the project root
- **THEN** matplotlib, Pillow, and pyxclip SHALL be installed automatically

#### Scenario: Entry point b3-selic-pre is created

- **WHEN** the package is installed
- **THEN** a console script `b3-selic-pre` SHALL be available in the environment that runs `b3_selic_pre.presentation.cli:main`

### Requirement: Icons are shipped as package data

The icon files SHALL be moved from `icons/` at the project root to `src/b3_selic_pre/icons/` and declared as `package_data` in `pyproject.toml`. The `_icon_source()` function SHALL use `importlib.resources` to locate the icon at runtime, with a fallback to `sys._MEIPASS` for frozen builds.

#### Scenario: Icon found at runtime in development mode

- **WHEN** the package is installed in editable mode and `_icon_source()` is called
- **THEN** it SHALL return a path to the PNG icon inside the installed package

#### Scenario: Icon found at runtime in frozen build

- **WHEN** `sys.frozen` is True and `_icon_source()` is called
- **THEN** it SHALL return a path under `sys._MEIPASS`

### Requirement: PyInstaller spec references new entry point

The `b3-selic-pre.spec` file SHALL be updated so that `Analysis` points to `src/b3_selic_pre/__main__.py` and `datas` includes the icon from the new location.

#### Scenario: PyInstaller compiles the frozen binary

- **WHEN** running `pyinstaller b3-selic-pre.spec`
- **THEN** the resulting binary SHALL execute the same application with identical behavior to the pre-refactor build

### Requirement: All consumers are updated

Makefile, GitHub Actions workflows (`test.yml`, `release.yml`), README.md, `.gitignore`, and OpenSpec skills (`release-version`, `release-push`) SHALL be updated to reflect the new package structure and build process.

#### Scenario: `make test` passes

- **WHEN** running `make test`
- **THEN** all unit tests SHALL pass with no import errors

#### Scenario: `make build` produces binary

- **WHEN** running `make build`
- **THEN** a frozen binary SHALL exist at `dist/b3-selic-pre`

#### Scenario: CI test workflow passes

- **WHEN** pushing to the `main` branch
- **THEN** the Lint and test workflow SHALL complete successfully

#### Scenario: CI release workflow builds all platforms

- **WHEN** triggering a release via tag push or `workflow_dispatch`
- **THEN** binaries for Linux, Windows, and macOS SHALL be produced and attached to the release

### Requirement: Tests import from specific modules

All test imports SHALL reference the specific module path (e.g., `from b3_selic_pre.domain.models import RateRecord`) and all `mock.patch` calls SHALL use the full dotted path to the target function after restructuring.

#### Scenario: All unit tests pass without re-exports

- **WHEN** running `pytest` with the restructured package
- **THEN** all existing tests SHALL pass without relying on re-exports from `b3_selic_pre.__init__`
