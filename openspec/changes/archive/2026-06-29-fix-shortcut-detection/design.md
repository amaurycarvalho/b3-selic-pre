## Context

The `shortcut_exists()` function in `infrastructure/desktop.py` checks only `SHORTCUT_CHECK_PATH` (`~/.local/share/applications/b3-selic-pre.desktop`) to decide whether to show the "Criar Atalho Desktop" button. The `create_shortcut()` function writes `.desktop` files to two locations: `~/Desktop/` and `~/.local/share/applications/`. If the applications entry exists but the Desktop shortcut does not (e.g., user deleted Desktop file, partial installation), the button is hidden and there is no way to recreate the Desktop shortcut through the GUI.

## Goals / Non-Goals

**Goals:**
- `shortcut_exists()` verifies both the Desktop shortcut and the applications menu entry exist
- The "Criar Atalho Desktop" button appears whenever either destination is missing
- Backward-compatible: existing shortcuts are not affected

**Non-Goals:**
- Changing the `create_shortcut()` function behavior (it already writes to both locations correctly)
- Adding cross-platform shortcut support (Windows/macOS)
- Removing or redesigning the applications entry check

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Which paths to check | Both `~/Desktop/b3-selic-pre.desktop` and `~/.local/share/applications/b3-selic-pre.desktop` | The button's purpose is to create a Desktop shortcut; if it's missing, the button should appear. Checking both ensures completeness. |
| How to resolve Desktop path | Reuse existing `_detect_desktop_dir()` | Avoids duplicating XDG detection logic; already handles pt-BR locale (`~/Área de Trabalho`) and fallbacks. |
| Where to add the Desktop path constant | In `shortcut_exists()` itself rather than `constants.py` | The Desktop path depends on runtime detection (`_detect_desktop_dir`), not a fixed value. A constant would be misleading. |
| Check logic | `AND` (both must exist) | The user needs both shortcuts to be considered fully installed. If either is missing, show the button. |

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| `_detect_desktop_dir()` may fail to find Desktop directory | Falls back to `~/Desktop` which is the standard default |
| Existing users with only `~/.local/share/applications/` file will see button reappear | This is intentional — they need the Desktop shortcut too |
