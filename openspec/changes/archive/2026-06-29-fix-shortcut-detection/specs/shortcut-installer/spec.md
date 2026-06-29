## MODIFIED Requirements

### Requirement: GUI shortcut button

When running in GUI mode, the system SHALL detect whether the shortcut exists in **both** `~/Desktop/` **and** `~/.local/share/applications/` and, if either is missing, show a "Criar Atalho Desktop" button.

#### Scenario: Button appears when no shortcut exists
- **WHEN** the user launches the GUI via `--gui`
- **AND** no `.desktop` file exists at either `~/Desktop/b3-selic-pre.desktop` or `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button appears when only applications entry exists
- **WHEN** the user launches the GUI via `--gui`
- **AND** a `.desktop` file exists at `~/.local/share/applications/b3-selic-pre.desktop`
- **AND** no `.desktop` file exists at `~/Desktop/b3-selic-pre.desktop`
- **THEN** a button labeled "Criar Atalho Desktop" is visible in the top frame

#### Scenario: Button is absent when both shortcuts exist
- **WHEN** the user launches the GUI via `--gui`
- **AND** `.desktop` files exist at both `~/Desktop/b3-selic-pre.desktop` and `~/.local/share/applications/b3-selic-pre.desktop`
- **THEN** the "Criar Atalho Desktop" button is NOT shown

#### Scenario: Button creates shortcut and disappears
- **WHEN** the user clicks "Criar Atalho Desktop"
- **THEN** a `.desktop` file is created in `~/Desktop/` and `~/.local/share/applications/`
- **AND** the button is removed from the GUI
