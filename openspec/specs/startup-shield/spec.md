# Startup Shield Specification

## Purpose

Cobrir a janela principal e bloquear a interação durante a inicialização da interface gráfica, deixando explícito para o usuário que a aplicação ainda está sendo preparada.

## Requirements

### Requirement: Startup shield display

During GUI initialization, the system SHALL display an opaque shield over the main window before the heavy interface construction begins, with the wait message "Aguarde a inicialização da aplicação…" centered in the window. The shield SHALL remain visible until the interface construction and first render are complete.

#### Scenario: Shield appears before controls are built

- **WHEN** the GUI starts and heavy interface construction (including chart setup) has not yet begun
- **THEN** the shield SHALL already be visible over the main window
- **AND** the wait message SHALL be centered in the window

#### Scenario: Shield is opaque

- **WHEN** the shield is visible
- **THEN** no control or content behind it SHALL be visible through the shield

### Requirement: Full coverage and stacking

The shield SHALL cover the entire usable area of the main toplevel, including the top controls bar (labels, date entry, buttons, and combobox-like controls), regardless of whether those controls are created before or after the shield. After the interface construction finishes, the shield SHALL be raised above all sibling widgets so that no control remains visible. When the window is resized while the shield is visible, the shield SHALL continue to cover the full usable area.

#### Scenario: Controls created after the shield do not appear above it

- **WHEN** the top controls bar and the remaining widgets are created after the shield
- **THEN** the shield SHALL remain visually above all of them
- **AND** no top-bar control SHALL be visible or reachable

#### Scenario: Window resize preserves coverage

- **WHEN** the window is resized or maximized while the shield is visible
- **THEN** the shield SHALL continue to cover the entire usable area of the window

### Requirement: Full interaction blocking

While the shield is visible, the system SHALL block pointer and keyboard interaction with the application. No click SHALL activate a control, no keyboard shortcut SHALL trigger an action, and Tab or Shift+Tab SHALL NOT move focus to a hidden control. Closing the application window SHALL remain permitted.

#### Scenario: Click on a top-bar control is blocked

- **WHEN** the user clicks the position of a top-bar control while the shield is visible
- **THEN** the shield SHALL receive the event
- **AND** the control SHALL NOT be activated

#### Scenario: Keyboard shortcut is blocked

- **WHEN** the user presses F5, Ctrl+D, Ctrl+Shift+C, Ctrl+E, or Ctrl+L while the shield is visible
- **THEN** the corresponding application action SHALL NOT run

#### Scenario: Focus does not escape the shield

- **WHEN** the user presses Tab or Shift+Tab while the shield is visible
- **THEN** focus SHALL remain on the shield
- **AND** no hidden control SHALL receive focus

#### Scenario: Window close remains available

- **WHEN** the user closes the window while the shield is visible
- **THEN** the application SHALL close normally

### Requirement: Tooltip suppression during startup

While the shield is visible, the system SHALL NOT display tooltips or other auxiliary popups above it, including tooltips associated with top-bar controls. Tooltips SHALL become available normally after the shield is removed.

#### Scenario: No tooltip appears above the shield

- **WHEN** a top-bar control would be eligible to show a tooltip during startup
- **THEN** no tooltip window SHALL be displayed above the shield

#### Scenario: Tooltips work after startup

- **WHEN** the shield has been removed and the user hovers a control that has a tooltip
- **THEN** the tooltip SHALL appear normally after the usual delay

### Requirement: Shield dismissal and restoration

After the interface construction and first render are complete, the system SHALL remove the shield after a short settle interval that allows events queued during construction to be processed. After removal, the system SHALL restore normal control states, global shortcuts, tooltips, and the initial status message. Events triggered while the shield was visible SHALL NOT be delivered to the application controls after removal.

#### Scenario: Shield is removed after startup

- **WHEN** the interface construction and first render complete
- **THEN** the shield SHALL be removed after the settle interval
- **AND** the initial status message SHALL be visible
- **AND** control states SHALL reflect the available data

#### Scenario: Shortcuts and tooltips are restored after removal

- **WHEN** the shield has been removed
- **THEN** global shortcuts SHALL be active
- **AND** tooltips SHALL be registered again

#### Scenario: Queued input does not leak to controls

- **WHEN** the user attempts an interaction while the shield is visible and the shield is then removed
- **THEN** the attempted interaction SHALL NOT trigger any control after removal
