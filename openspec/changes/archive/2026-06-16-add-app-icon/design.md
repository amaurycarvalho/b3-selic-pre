## Context

The `b3_selic_pre.py` script has a Tkinter GUI (SelicPreApp class) launched via `--gui`. Currently the window shows a default Tkinter icon. A 64×64 PNG icon (`b3_selic_pre.png`) exists at the project root but is not loaded. There is no `.desktop` file for desktop environment integration.

## Goals / Non-Goals

**Goals:**
- Display `b3_selic_pre.png` as the Tkinter window icon (title bar, taskbar, alt-tab)
- Resolve the icon path robustly regardless of working directory
- Provide a `.desktop` file for Linux desktop environments
- Keep the original PNG as the single icon source (no `.ico` conversion)

**Non-Goals:**
- Packaging/distribution (PyInstaller, etc.)
- Windows `.ico` or macOS `.icns` formats
- Changing the icon used for the chart or exported images
- System-wide installation of the `.desktop` file

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tkinter icon method | `iconphoto(True, photo)` with `tk.PhotoImage` | `iconbitmap` requires `.ico` on Windows. Since we want to keep PNG, `iconphoto` is the cross-platform choice. `True` applies the icon to all future toplevel windows too. |
| Path resolution | Resolve relative to `__file__` using `os.path.dirname(os.path.abspath(__file__))` | Ensures the icon is found regardless of the user's CWD when launching the script |
| .desktop file location | Project root (`b3-selic-pre.desktop`) | The user can copy it to `~/.local/share/applications/` manually — the project itself should not modify system directories |
| .desktop Exec path | Use `bash -c` wrapper resolving to script dir, or document that user must edit the path | Absolute paths are fragile; relative paths don't work in `.desktop` files |

## Risks / Trade-offs

- **[Portability]** `iconphoto` works on all platforms Tkinter supports, but the `.desktop` file is Linux-specific. macOS users would need a different launcher mechanism (`.app` bundle). **Mitigation**: Document that `.desktop` is Linux-only; other platforms can run `--gui` directly.
- **[Path breaking]** If the script is moved after the `.desktop` file is created, the `Exec` path becomes stale. **Mitigation**: Use a symlink-friendly resolution and document this in the `.desktop` file as a comment.
- **[PhotoImage GC]** Tkinter's `PhotoImage` gets garbage-collected if not assigned to a persistent reference. **Mitigation**: Store the `PhotoImage` as `self.icon_img` on the `SelicPreApp` instance.
