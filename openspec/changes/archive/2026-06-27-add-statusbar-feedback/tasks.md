## 1. Statusbar Widget

- [x] 1.1 Create `statusbar_frame` as a `ttk.Frame` packed at root level (after `bottom_frame`) with `fill=tk.X`
- [x] 1.2 Move the status `ttk.Label` from `bottom_frame` (line 219-224) into the new `statusbar_frame`, preserving `textvariable=self.status_var` and full-width expansion
- [x] 1.3 Apply a visual separator between `bottom_frame` and the statusbar (e.g., `ttk.Separator` or a subtle border via `padding`/`relief`)

## 2. Message Type Styling

- [x] 2.1 Update `set_status()` signature to `set_status(self, message, msg_type="info")`
- [x] 2.2 Add foreground color mapping: `info` → system default, `success` → `"green"`, `warning` → `"orange"`, `error` → `"red"`
- [x] 2.3 Apply `label.config(foreground=color)` in `set_status()` based on `msg_type`

## 3. Update Call Sites

- [x] 3.1 Tag error calls (`ValueError` at line 353, `handle_fetch_error` at line 426) with `msg_type="error"`
- [x] 3.2 Tag warning calls ("Data muito antiga" at line 358, clipboard fallback at line 443) with `msg_type="warning"`
- [x] 3.3 Tag success calls (shortcut created at line 263, records loaded at line 405, historical loaded at line 419, chart copied at line 441, data copied at line 457, PNG exported at line 472) with `msg_type="success"`
- [x] 3.4 Info calls (initial message, loading, progress, empty results) keep the default `msg_type="info"` — no change needed

## 4. Update Tests

- [x] 4.1 Update existing tests in `tests/test_b3_selic_pre_gui.py` that reference `status_var` to assert on the new statusbar widget behavior
