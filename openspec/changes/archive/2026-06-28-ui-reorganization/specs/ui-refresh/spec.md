## ADDED Requirements

### Requirement: DateEntry replaces custom DatePicker
The system SHALL use `tkcalendar.DateEntry` instead of `ttk.Entry` + calendar button + custom `DatePicker` class for date input.

#### Scenario: DateEntry displays dropdown calendar
- **WHEN** user clicks the DateEntry dropdown arrow
- **THEN** a calendar popup SHALL appear below the entry field

#### Scenario: DateEntry accepts typed input
- **WHEN** user types a date in YYYY-MM-DD format
- **THEN** the DateEntry SHALL accept the typed value

#### Scenario: DateEntry validates dates
- **WHEN** user types an invalid date
- **THEN** the DateEntry SHALL reject the input (tkcalendar default validation)

### Requirement: Icon buttons replace text buttons
The system SHALL display icon-only buttons (24×24 PNG) for Hoje, Buscar, Copiar dados, and Copiar gráfico, replacing their text labels.

#### Scenario: Hoje button shows document-open-recent icon
- **WHEN** the application starts
- **THEN** the "Hoje" button SHALL display `document-open-recent.png` icon

#### Scenario: Buscar button shows view-refresh icon
- **WHEN** the application is idle
- **THEN** the "Buscar" button SHALL display `view-refresh.png` icon

#### Scenario: Buscar button shows content-loading during fetch
- **WHEN** a fetch operation is in progress
- **THEN** the "Buscar" button SHALL display `content-loading.png` icon

#### Scenario: Copiar dados button shows edit-copy icon
- **WHEN** the application starts
- **THEN** the "Copiar dados" button SHALL display `edit-copy.png` icon

#### Scenario: Copiar gráfico button shows edit-copy icon
- **WHEN** the application starts
- **THEN** the "Copiar gráfico" button SHALL display `edit-copy.png` icon

#### Scenario: All icon buttons have tooltips
- **WHEN** user hovers over an icon button
- **THEN** a tooltip SHALL appear with the functional description

### Requirement: Buscar loading state shows statusbar message
The system SHALL display "Buscando…" in the statusbar during fetch operations, not on the button itself.

#### Scenario: Statusbar shows Buscando during fetch
- **WHEN** a fetch operation starts
- **THEN** the statusbar SHALL display "Buscando…" message

#### Scenario: Statusbar clears on fetch complete
- **WHEN** a fetch operation completes
- **THEN** the statusbar SHALL update with success/error message

### Requirement: Copiar dados button on top row
The "Copiar dados" button SHALL be positioned in the top_frame, immediately after the "Buscar" button.

#### Scenario: Copiar dados is after Buscar
- **WHEN** the application starts
- **THEN** "Copiar dados" button SHALL appear to the right of the "Buscar" button in the top frame

### Requirement: Copiar gráfico in matplotlib toolbar
The "Copiar gráfico" button SHALL be inside the matplotlib `NavigationToolbar2Tk`, after the native buttons.

#### Scenario: Copiar gráfico appears in toolbar
- **WHEN** the application starts
- **THEN** the "Copiar gráfico" icon button SHALL appear in the matplotlib toolbar

#### Scenario: Copiar gráfico copies chart to clipboard
- **WHEN** user clicks "Copiar gráfico"
- **THEN** the current chart SHALL be copied to the clipboard as an image (via pyxclip)

### Requirement: Exportar PNG removed
The "Exportar PNG" button SHALL NOT exist. The matplotlib native toolbar "Save" button provides equivalent functionality.

#### Scenario: No Exportar PNG button
- **WHEN** the application starts
- **THEN** no "Exportar PNG" button SHALL appear anywhere in the UI

### Requirement: Middle row merges radiobuttons, checkboxes, and stats
The radiobuttons, checkboxes, and stats summary SHALL occupy a single reduced-height row between the top frame and the chart pane.

#### Scenario: Radiobuttons on left of middle row
- **WHEN** the application starts
- **THEN** "Detalhado" and "Consolidado" radiobuttons SHALL appear on the left side of the middle row

#### Scenario: Checkboxes on left of middle row
- **WHEN** the application starts
- **THEN** "Evolução da curva", "3D", and "Análise" checkboxes SHALL appear on the left side of the middle row

#### Scenario: Stats on right of middle row
- **WHEN** data is loaded
- **THEN** the stats summary SHALL appear on the right side of the middle row, pipe-separated

#### Scenario: Stats format is compact
- **WHEN** data is loaded
- **THEN** stats SHALL display in format `Data: YYYY-MM-DD | N reg | X,XX% | Y,YY% | Z venc`

### Requirement: Window title is frozen
The window title SHALL remain `B3 SELIC Pré v{version}` and SHALL NOT change after data load, historical fetch, or error.

#### Scenario: Title unchanged after data load
- **WHEN** data is loaded successfully
- **THEN** the window title SHALL remain `B3 SELIC Pré v{version}`

#### Scenario: Title unchanged after error
- **WHEN** a fetch error occurs
- **THEN** the window title SHALL remain `B3 SELIC Pré v{version}`

### Requirement: tkcalendar dependency added
The project SHALL declare `tkcalendar` as a dependency in `pyproject.toml` and include it in the PyInstaller build.

#### Scenario: tkcalendar in pyproject.toml
- **WHEN** the project is built or installed
- **THEN** `tkcalendar` SHALL be resolved as a dependency

#### Scenario: PyInstaller build includes tkcalendar
- **WHEN** the project is packaged with PyInstaller
- **THEN** `tkcalendar` SHALL be included in `hiddenimports` and the frozen executable SHALL work
