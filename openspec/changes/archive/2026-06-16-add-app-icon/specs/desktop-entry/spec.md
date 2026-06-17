## Purpose

Provide a FreeDesktop-compatible `.desktop` entry file so the application can be launched from the system application menu on Linux desktop environments.

## Requirements

### Requirement: Desktop entry file
The project SHALL include a `b3-selic-pre.desktop` file at the project root following the FreeDesktop Desktop Entry Specification.

#### Scenario: Desktop file exists at project root
- **WHEN** the user checks the project root directory
- **THEN** a file named `b3-selic-pre.desktop` is present

### Requirement: Desktop entry properties
The `.desktop` file SHALL define the application name, icon, and launch command for the GUI.

#### Scenario: Desktop entry contains mandatory fields
- **WHEN** the user inspects the `.desktop` file
- **THEN** it contains valid `Name`, `Exec`, `Icon`, `Type`, and `Categories` fields

#### Scenario: Desktop entry uses the PNG as its icon
- **WHEN** the `.desktop` file is installed and displayed in the application menu
- **THEN** the menu entry shows `b3_selic_pre.png` as its icon
