## MODIFIED Requirements

### Requirement: GUI collapsible sidebar
The system SHALL provide a collapsible sidebar panel on the right side of the GUI window that displays the analysis report. The panel SHALL start expanded on the first run, when no settings file exists, and SHALL start collapsed on subsequent runs. It SHALL expand/collapse via a toggle button.

#### Scenario: Sidebar starts expanded on first run
- **WHEN** the application starts and the settings file does not exist
- **THEN** the analysis panel SHALL start expanded and display the report area

#### Scenario: Sidebar starts collapsed on subsequent runs
- **WHEN** the application starts and the settings file exists
- **THEN** the analysis panel SHALL start collapsed unless the saved sidebar preference is enabled

#### Scenario: Sidebar toggles open
- **WHEN** the user clicks the toggle button "▶ Análise"
- **THEN** the sidebar expands to display the report text in a readonly widget

#### Scenario: Sidebar toggles closed
- **WHEN** the user clicks the toggle button "▼ Análise" while the sidebar is open
- **THEN** the sidebar collapses, hiding the report text
