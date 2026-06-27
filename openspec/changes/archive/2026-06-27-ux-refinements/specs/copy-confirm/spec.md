## ADDED Requirements

### Requirement: Temporary copy confirmation
The system SHALL display a copy confirmation message that reverts to the prior status after 2 seconds.

#### Scenario: Copy confirmation shown
- **WHEN** the user clicks "Copiar dados" or "Copiar gráfico"
- **THEN** the statusbar SHALL display the appropriate confirmation message (e.g., "✓ Dados copiados")

#### Scenario: Prior status restored
- **WHEN** 2 seconds have elapsed
- **THEN** the statusbar SHALL revert to the message that was displayed before the copy action
- **THEN** the statusbar foreground color SHALL revert to its previous value
