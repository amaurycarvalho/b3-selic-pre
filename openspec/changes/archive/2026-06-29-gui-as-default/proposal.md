## Why

Users expect a desktop application to launch its GUI when invoked without arguments. Currently `b3-selic-pre` (no args) prints CSV to stdout, which is counter-intuitive for a packaged app with a GUI. Making GUI the default improves the out-of-box experience while keeping CLI mode accessible via explicit arguments.

## What Changes

- **BREAKING**: `b3-selic-pre` (no args) now opens the GUI instead of printing CSV
- `b3-selic-pre --today` prints today's rates as CSV (restores the old bare-invocation behavior explicitly)
- `--gui` flag continues to work as before (redundant but kept for backward compatibility with existing shortcuts/scripts)
- Desktop shortcut continues to use `--gui` explicitly (no change needed)
- `b3-selic-pre <date>`, `--yearly`, `--create-shortcut`, `--version` all unchanged

## Capabilities

### New Capabilities
- `cli-default-mode`: Controls whether CLI or GUI is the default invocation mode, and provides explicit flags for each.

### Modified Capabilities
*(none — no existing spec requirements are changing)*

## Impact

- `src/b3_selic_pre/presentation/cli.py` — main() entry point logic
- `tests/test_b3_selic_pre.py` — may need new tests for the bare-invocation path
- README / docs — should reflect new default behavior
- Users/scripts relying on bare `b3-selic-pre` for CSV output will break (mitigated by `--today`)
