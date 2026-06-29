## Context

Currently `cli.py:main()` delegates to `parse_args()` which uses argparse. The `--gui` flag is `store_true` with default `False`, so bare invocation always runs CLI mode. The change inverts this: bare invocation launches GUI, and CLI mode is entered only when explicit arguments are given.

The codebase has a clear `presentation/cli.py` → `presentation/gui.py` boundary. The change is isolated to `cli.py` (the entry point and arg parsing).

## Goals / Non-Goals

**Goals:**
- Bare `b3-selic-pre` opens GUI
- `--today` flag provides explicit CSV output for today's date
- All existing flags (`--yearly`, `--create-shortcut`, `--version`, `--gui`) continue working
- Minimal code change — no refactoring of GUI or data layers

**Non-Goals:**
- Removing the `--gui` flag (kept for backward compatibility)
- Changing the desktop shortcut generation logic (keeps `--gui`)
- Refactoring argument parsing library (stays with argparse)
- Any GUI-side changes

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| How to detect "no args" | Check `len(argv) == 0` before argparse | Simple, explicit, doesn't require argparse changes. Argparse with `nargs="?"` and a default can't distinguish "user didn't pass date" from "user passed the default date" after parsing. |
| Flag name for explicit today's CSV | `--today` | Clear, self-documenting, matches user's request. Alternative `--cli` was considered but is ambiguous (CLI mode with what date?). |
| Preserve `--gui` flag | Keep as-is | Already works, used by existing shortcuts. Removing it would break nothing but adds unnecessary risk. |

```
main(argv)
  │
  ├─ argv = sys.argv[1:]  (if argv is None)
  │
  ├─ len(argv) == 0? ──YES──→ launch_gui() + return  ← NEW
  │
  └─ parse_args(argv)
       ├─ --create-shortcut? → create_shortcut()
       ├─ --gui? → launch_gui()
       ├─ --today? → use today's date + CLI output
       └─ (default CLI) → fetch + print
```

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| **BREAKING**: scripts using bare `b3-selic-pre` hang waiting for GUI | Documented as breaking change; `--today` provides migration path |
| `--gui` + `--today` or `--gui` + `<date>` are contradictory | The current early-return logic (shortcut → gui → cli) already handles this: `--gui` wins and exits before CLI actions |
| `--today` overlaps with the positional `date` argument | `--today` sets the date internally to today; if both `--today` and a date are given, `--today` wins or argparse error. We'll make them mutually exclusive in argparse via a custom group or post-check. |
