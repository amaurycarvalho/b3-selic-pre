## 1. Modify CLI entry point

- [x] 1.1 In `main()`, intercept bare invocation (no args) to launch GUI before argparse
- [x] 1.2 Add `--today` argument to argparse (store_true, mutually exclusive with positional `date`)
- [x] 1.3 Handle `--today` in main(): set date to today, fall through to CLI output path

## 2. Update tests

- [x] 2.1 Add test: bare `main()` call launches GUI
- [x] 2.2 Add test: `main(["--today"])` prints today's CSV
- [x] 2.3 Add test: `main(["--today", "--yearly"])` prints yearly CSV
- [x] 2.4 Add test: `main(["--gui"])` still launches GUI
- [x] 2.5 Verify existing tests still pass

## 3. Verify

- [x] 3.1 Run full test suite (65 passed, 0 failed)
- [x] 3.2 Manual check: `b3-selic-pre` opens GUI; `b3-selic-pre --today` prints CSV; existing flags unchanged
