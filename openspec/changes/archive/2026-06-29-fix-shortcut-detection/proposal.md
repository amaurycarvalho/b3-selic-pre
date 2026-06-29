## Why

The "Criar Atalho Desktop" button does not appear when `~/.local/share/applications/b3-selic-pre.desktop` exists but the Desktop shortcut (`~/Desktop/b3-selic-pre.desktop`) is missing. This leaves users without a way to recreate the Desktop shortcut through the GUI.

## What Changes

- Modify `shortcut_exists()` in `desktop.py` to check **both** shortcut destinations (`~/Desktop/` and `~/.local/share/applications/`) instead of only the applications entry
- The "Criar Atalho Desktop" button will appear whenever either shortcut is missing, allowing the user to recreate incomplete installations
- Update `shortcut-installer` spec to reflect the corrected detection behavior

## Capabilities

### New Capabilities

*(none)*

### Modified Capabilities

- `shortcut-installer`: Change the GUI shortcut detection to verify both the Desktop shortcut and the applications menu entry exist, not just the applications entry alone

## Impact

- **Target**: Release 0.8.4
- `src/b3_selic_pre/infrastructure/desktop.py` — `shortcut_exists()` logic
- `src/b3_selic_pre/domain/constants.py` — may need additional constant for Desktop path
- `openspec/specs/shortcut-installer/spec.md` — update detection requirement and scenarios
- `tests/test_b3_selic_pre.py` — update tests to match new behavior
