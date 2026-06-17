## Why

The desktop GUI currently has no window icon — it appears with the default Tkinter logo in the title bar and taskbar. The `b3_selic_pre.png` asset already exists at the project root but is unused. Adding it as the application icon improves visual identity and professionalism. A `.desktop` file enables users to launch the app from their system application menu.

## What Changes

- Set the Tkinter window icon to `b3_selic_pre.png` using `iconphoto` (cross-platform PNG support)
- Resolve the icon path relative to the script directory to work from any CWD
- Create a `.desktop` entry file for launching the GUI from system menus
- Add a CLI helper or convenience script if `.desktop` needs an absolute entry point

## Capabilities

### New Capabilities
- `app-icon`: Application icon for the Tkinter window — loading and setting the PNG icon on the root window, including proper path resolution
- `desktop-entry`: Cross-platform desktop entry for launching the GUI from the system application menu

### Modified Capabilities
*(none — no existing spec requirements are changing)*

## Impact

- `b3_selic_pre.py`: small addition in `SelicPreApp.__init__` to load and set the icon
- New file: `b3-selic-pre.desktop` at project root (or platform-appropriate location)
- No new dependencies required (Tkinter's `PhotoImage` is built-in)
