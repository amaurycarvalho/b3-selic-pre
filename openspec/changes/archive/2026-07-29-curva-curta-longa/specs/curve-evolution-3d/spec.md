## MODIFIED Requirements

### Requirement: Title positioned centered over chart
The system SHALL set the 3D title with horizontal centering so the title appears centered over the chart area.

#### Scenario: 3D title is centered horizontally
- **WHEN** the 3D evolution title is set
- **THEN** the title's `ha` parameter is set to `"center"`
- **AND** no artificial horizontal offset is applied to the title position

### REMOVED Requirements

### Requirement: Title positioned over chart area (not colorbar)
**Reason**: Replaced by centered title requirement above. The previous behavior shifted the title left via `t.set_x(0.5 - 0.7 * w_ax)` to avoid the colorbar, but the new design requires horizontal centering.
**Migration**: Set `ha="center"` on the title instead of applying the `set_x` offset.
