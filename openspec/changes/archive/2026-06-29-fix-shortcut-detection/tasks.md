## 1. Detection Logic

- [x] 1.1 Modify `shortcut_exists()` in `src/b3_selic_pre/infrastructure/desktop.py` to check both `~/.local/share/applications/b3-selic-pre.desktop` and the Desktop file resolved via `_detect_desktop_dir()`
- [x] 1.2 Update `SHORTCUT_CHECK_PATH` constant comment or add a helper if needed in `src/b3_selic_pre/domain/constants.py`

## 2. Spec Update

- [x] 2.1 Update `openspec/specs/shortcut-installer/spec.md` to reflect the new dual-path detection behavior

## 3. Tests

- [x] 3.1 Update `shortcut_exists()` tests in `tests/test_b3_selic_pre.py` to cover scenarios: both exist, only applications exists, only Desktop exists, neither exists
- [x] 3.2 Update GUI tests in `tests/test_b3_selic_pre_gui.py` if they assert old detection behavior

## 4. Verification

- [x] 4.1 Run existing tests to confirm no regressions
- [x] 4.2 Launch the GUI with `--gui` and confirm the button appears when the Desktop shortcut is missing
