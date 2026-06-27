## Why

The application's feedback messages are currently displayed as a plain `ttk.Label` alongside action buttons in the bottom frame, with no visual distinction between errors, warnings, successes, or informational messages. This makes it hard for users to quickly identify the nature of feedback and clutters the button area. A dedicated statusbar at the bottom of the window solves this by providing a clear, standardized area for all status messages, with appropriate visual cues for different message severities.

## What Changes

- Replace the existing plain `ttk.Label` status message with a proper statusbar widget at the window's base.
- The statusbar will visually differentiate message types (info, success, warning, error) using foreground colors and/or icons.
- Update all `set_status()` call sites to pass a message type so the statusbar renders appropriate styling.
- Keep the statusbar API simple: `set_status(message, type="info")` where type defaults to `"info"`.
- The existing message label position (inline in `bottom_frame`) will be removed; the statusbar sits at the very bottom of the window.
- No new dependencies required — the statusbar will be built with standard `ttk` widgets.

## Capabilities

### New Capabilities
- `statusbar`: A dedicated statusbar at the window's base that displays application feedback with visual differentiation for info, success, warning, and error messages.

### Modified Capabilities
<!-- No existing specs to modify — this is a purely presentational change. -->

## Impact

- **File changed**: `src/b3_selic_pre/presentation/gui.py` — refactor `bottom_frame` layout, replace status label with statusbar, update `set_status()` signature and all call sites.
- **Tests**: `tests/test_b3_selic_pre_gui.py` — may need updates if tests assert on the old status label behavior.
- **No API/dependency changes**: the CLI, domain, and infrastructure layers are unaffected.
