## Context

The GUI currently places a plain `ttk.Label` bound to `status_var` in the `bottom_frame`, inline with action buttons and view-mode toggles. All 17 `set_status()` call sites pass a plain string with no type information. The message area has no visual differentiation for error vs. success vs. informational messages.

The project uses standard `tkinter`/`ttk` with no external widget libraries, and this change must not introduce new dependencies.

## Goals / Non-Goals

**Goals:**
- Provide a dedicated statusbar area at the very bottom of the window, visually separated from the button/toggle area.
- Support four message types: `info` (default), `success`, `warning`, `error`.
- Apply distinct foreground colors per type: info=system default, success=green, warning=orange, error=red.
- Keep the existing `set_status(message)` API signature; add an optional `msg_type` parameter defaulting to `"info"`.
- Preserve all existing feedback messages unchanged in content — only the display changes.

**Non-Goals:**
- No auto-timeout or auto-clear mechanism (messages persist until overwritten, as today).
- No message history or log panel.
- No icon support in this iteration.
- No animation or transition effects.

## Decisions

1. **Separate `ttk.Frame` at window root level** for the statusbar, instead of embedding inside `bottom_frame`.
   - Rationale: The statusbar should span the full window width and be visually distinct from the action-button area. Packing it at the root level (after `bottom_frame`) ensures it always sits at the very bottom.

2. **`ttk.Label` inside the statusbar frame** rather than a custom widget.
   - Rationale: Matches existing code style, no new dependencies, sufficient for text + foreground color changes.

3. **Foreground color changes via `label.config(foreground=...)`** as the sole visual differentiator.
   - Rationale: Simplest approach in tkinter. Can be enhanced with icons later without breaking the API.

4. **Optional `msg_type` parameter** with string enum-like values (`"info"`, `"success"`, `"warning"`, `"error"`).
   - Rationale: Minimal API surface. The 17 existing call sites need only `msg_type` added at relevant locations (errors, successes, etc.), while others keep the default.

5. **Keep `status_var` as the backing variable** for text content.
   - Rationale: Minimal refactoring — only the display widget changes, not the data flow.

## Risks / Trade-offs

- **Risk**: Color contrast may be poor on some system themes. → Mitigation: Use standard named colors (`green`, `orange`, `red`) that adapt reasonably across themes. Could switch to `ttk.Style` theming in the future.
- **Trade-off**: No auto-clear means a transient success message ("Gráfico copiado") stays visible until the next action. Acceptable for MVP; auto-clear can be added later.
- **Trade-off**: Using `foreground` color only (no background or border) means colorblind users may not distinguish types visually. Acceptable for now; icon support is a future enhancement.
