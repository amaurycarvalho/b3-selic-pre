## Context

The `SelicPreApp` tkinter GUI in `b3_selic_pre.py` already has two data-export buttons ("Copiar gráfico" for chart image, "Exportar PNG" for file save). The underlying data (`self.records`) and formatters (`format_cli_rows`, `format_yearly_rows`) already exist. What's missing is a way to copy the CSV behind the current chart view to the clipboard.

## Goals / Non-Goals

**Goals:**
- Add a "Copiar dados" button that copies CSV of the current view (raw or consolidated) to the clipboard
- Reuse existing CSV formatters (`format_cli_rows`, `format_yearly_rows`)
- Use tkinter's cross-platform clipboard API (`clipboard_clear` + `clipboard_append`)
- Follow the existing button pattern (disabled when no data, status feedback after copy)

**Non-Goals:**
- No file-save dialog (clipboard-only)
- No new output formats (matches existing CLI CSV conventions exactly)
- No changes to the CLI path

## Decisions

| Decision | Choice | Alternatives Considered |
|---|---|---|
| **Clipboard API** | tkinter's built-in `root.clipboard_clear()` + `root.clipboard_append()` | `subprocess` with `xclip`/`pbcopy` — unnecessary complexity; tkinter handles cross-platform natively |
| **CSV formatter reuse** | `format_cli_rows()` for raw mode, `format_yearly_rows()` for consolidated | Writing new formatters — duplicate logic; existing functions already produce the desired output |
| **Button placement** | Before "Copiar gráfico", same `bottom_frame` | After "Copiar gráfico" — user explicitly requested before |
| **Button label** | "Copiar dados" | "Copiar CSV" — user explicitly specified |

## Risks / Trade-offs

- **tkinter clipboard is display-dependent**: On Linux, clipboard access requires a running X/Wayland display. This is inherent to GUI apps and matches existing behavior (the whole app already needs a display). No new risk.
- **Large datasets**: If B3 returns hundreds of pages, the CSV string could be large. This is the same data already held in `self.records`, so memory impact is minimal.
