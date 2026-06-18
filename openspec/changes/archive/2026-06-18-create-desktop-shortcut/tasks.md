## 1. Utility Functions

- [x] 1.1 Implement `_detect_desktop_dir()`: detect Desktop path via `xdg-user-dir` → `~/.config/user-dirs.dirs` → `~/Desktop`
- [x] 1.2 Implement `_resolve_executable()`: return the correct Exec command for frozen (PyInstaller) vs script mode
- [x] 1.3 Implement `_icon_source()`: resolve icon path from `sys._MEIPASS` (frozen) or `_SCRIPT_DIR/icons/` (script)
- [x] 1.4 Implement `shortcut_exists()`: check if `~/.local/share/applications/b3-selic-pre.desktop` exists
- [x] 1.5 Implement `create_shortcut()`: orchestrate icon copy, `.desktop` content generation, and file writes to both destinations

## 2. CLI Integration

- [x] 2.1 Add `--create-shortcut` argument to `parse_args()`
- [x] 2.2 Add `--create-shortcut` handling to `main()`: call `create_shortcut()`, print confirmation, return

## 3. GUI Integration

- [x] 3.1 Add shortcut detection and conditional button creation in `SelicPreApp.__init__()` (top_frame, right side)
- [x] 3.2 Implement button callback `_create_shortcut()` that calls `create_shortcut()` and removes the button

## 4. Version & Housekeeping

- [x] 4.1 Bump `__version__` from `0.3.0` to `0.4.0`
- [x] 4.2 Update `b3-selic-pre.desktop` in project root to use `Name=Taxas Referenciais SELIC (B3)` and confirm `Categories=Finance;Office;`
- [x] 4.3 Sync main specs: update `openspec/specs/desktop-entry/spec.md` and `openspec/specs/app-icon/spec.md` with new requirements from delta specs

## 5. Tests

- [x] 5.1 Add test for CLI `--create-shortcut` flow (mock filesystem operations)
- [x] 5.2 Add test that GUI button appears when shortcut does not exist
- [x] 5.3 Add test that GUI button is absent when shortcut exists
- [x] 5.4 Add test that button callback creates shortcut and removes itself
- [x] 5.5 Add test for `_detect_desktop_dir()` with mocked `xdg-user-dir` output
- [x] 5.6 Add test for `_resolve_executable()` in both frozen and script modes
