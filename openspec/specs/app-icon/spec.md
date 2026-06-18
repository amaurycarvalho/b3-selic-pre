## Purpose

Display a custom application icon (b3_selic_pre.png) on the Tkinter GUI window, replacing the default Tkinter logo, to improve visual identity and user experience.

## Requirements

### Requirement: Window icon from PNG
The system SHALL set the Tkinter root window icon using `b3_selic_pre.png` via the cross-platform `iconphoto` method.

#### Scenario: Icon displayed on window launch
- **WHEN** the user launches the GUI with `--gui`
- **THEN** the Tkinter window displays `b3_selic_pre.png` as its icon in the title bar and taskbar

#### Scenario: Icon resists garbage collection
- **WHEN** the Tkinter window is open
- **THEN** the icon remains visible because the `PhotoImage` object is retained as an instance attribute

### Requirement: Robust icon path resolution
The system SHALL resolve the icon path relative to the script file location, not the current working directory.

#### Scenario: Script launched from another directory
- **WHEN** the user runs `python3 /path/to/b3_selic_pre.py --gui` from a different working directory
- **THEN** the icon is still found and displayed correctly

### Requirement: Icon copy for shortcut
When creating a desktop shortcut, the system SHALL copy `b3_selic_pre.png` to `~/.local/share/icons/` for stable reference by the `.desktop` file.

#### Scenario: Icon copied during shortcut creation
- **WHEN** the user creates a shortcut (via CLI `--create-shortcut` or GUI button)
- **THEN** the icon file `b3_selic_pre.png` is copied to `~/.local/share/icons/b3-selic-pre.png`

#### Scenario: Icon source resolution in frozen mode
- **WHEN** the application is running as a compiled PyInstaller binary
- **AND** the user creates a shortcut
- **THEN** the icon is resolved from the PyInstaller bundle directory (`sys._MEIPASS`)
