# AGENTS.md

## Project

`b3-selic-pre` is a Python desktop/CLI application organized in Clean Architecture layers under `src/b3_selic_pre/`:

- `domain/`: pure models and constants; no I/O, UI, network, or frameworks.
- `application/`: business rules, analysis, formatting, and headless services; no `presentation`, `infrastructure`, Tkinter, matplotlib, or network clients.
- `infrastructure/`: adapters for B3, disk cache, desktop integration; no UI.
- `presentation/`: CLI, GUI, settings, view-model, and chart rendering; may use `domain` and `application`.

Executable entry points and CLI composition roots may wire infrastructure explicitly.

## Architecture guardrails

- `tests/test_architecture.py` enforces layer boundaries and internal-layer purity using static AST analysis.
- Known debt must be registered in `tests/architecture_allowlist.py` with a reason. Adding an entry requires explicit review approval; stale entries fail the test and must be removed.
- `tests/test_ui_test_budget.py` enforces the UI test budget. Tests that import Tkinter or the GUI must be marked `@pytest.mark.ui`. Do not increase the budget; prefer headless tests and lower the budget when migrating.
- New behavior should be implemented in `application`/`presentation` headless modules whenever it can be shared by the GUI and future CLI commands.

## Change validation protocol

Every change MUST finish with:

1. `make lint`
2. `make complexity`
3. The tests directly related to the impacted code

Run the full test suite (`make test`) only when the change touches shared code or contracts that can cause application-wide regressions, for example:

- `domain` models/constants
- interfaces between layers
- shared infrastructure or cache behavior
- global GUI/CLI behavior
- build, packaging, or test configuration that affects the whole suite

If the full suite is not justified, the change MUST include, as its final task, an optional manual test step for the user describing what to verify.

A change is not complete while `make lint`, `make complexity`, or any directly related test fails.

## Specs

See `openspec/specs/` for the complete app specification.
