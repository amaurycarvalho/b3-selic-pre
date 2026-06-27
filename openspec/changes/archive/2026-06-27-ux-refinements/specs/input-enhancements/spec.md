## ADDED Requirements

### Requirement: Date validation visual feedback
The system SHALL visually highlight the date entry when validation fails.

#### Scenario: Red highlight on invalid date
- **WHEN** the user enters an invalid date and clicks "Buscar"
- **THEN** the date entry SHALL show a red background highlight

#### Scenario: Highlight cleared on correction
- **WHEN** the user corrects the date and the next validation succeeds
- **THEN** the red highlight SHALL be removed

### Requirement: Placeholder text in date entry
The system SHALL show placeholder text in the date entry when empty.

#### Scenario: Placeholder shown when empty
- **WHEN** the date entry is empty and unfocused
- **THEN** gray hint text "AAAA-MM-DD" SHALL be visible

#### Scenario: Placeholder hidden on focus
- **WHEN** the date entry receives focus
- **THEN** the placeholder text SHALL be removed

### Requirement: "Hoje" button
The system SHALL provide a button to reset the date to today.

#### Scenario: Hoje sets today's date
- **WHEN** the user clicks "Hoje"
- **THEN** the date entry SHALL be set to today's date in YYYY-MM-DD format

#### Scenario: Hoje triggers fetch
- **WHEN** the user clicks "Hoje"
- **THEN** a data fetch SHALL be initiated for today's date
