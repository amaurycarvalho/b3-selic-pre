## ADDED Requirements

### Requirement: Statusbar display
The system SHALL display a statusbar at the bottom of the main window, spanning the full window width, visually separated from action buttons and controls.

#### Scenario: Statusbar occupies bottom of window
- **WHEN** the application window is rendered
- **THEN** a statusbar frame SHALL be visible at the very bottom of the window

#### Scenario: Statusbar spans full width
- **WHEN** the application window is rendered
- **THEN** the statusbar SHALL extend the full width of the window

### Requirement: Message display
The system SHALL display feedback messages in the statusbar.

#### Scenario: Initial message shown
- **WHEN** the application starts
- **THEN** the statusbar SHALL display "Informe uma data e clique em Buscar."

#### Scenario: Message updates on user action
- **WHEN** `set_status()` is called with a message string
- **THEN** the statusbar SHALL display the new message

### Requirement: Message type styling
The system SHALL apply distinct visual styling to messages based on their type.

#### Scenario: Info message default
- **WHEN** `set_status("message")` is called without `msg_type`
- **THEN** the statusbar SHALL display the message with default (system) foreground color

#### Scenario: Success message
- **WHEN** `set_status("message", msg_type="success")` is called
- **THEN** the statusbar SHALL display the message in green foreground

#### Scenario: Warning message
- **WHEN** `set_status("message", msg_type="warning")` is called
- **THEN** the statusbar SHALL display the message in orange foreground

#### Scenario: Error message
- **WHEN** `set_status("message", msg_type="error")` is called
- **THEN** the statusbar SHALL display the message in red foreground

### Requirement: API backward compatibility
The `set_status()` method SHALL accept a positional message string with an optional `msg_type` keyword parameter defaulting to `"info"`.

#### Scenario: Legacy calls work unchanged
- **WHEN** `set_status("some message")` is called (as existing code does)
- **THEN** the message SHALL be displayed with `"info"` styling
