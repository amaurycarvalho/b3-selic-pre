## Purpose

Provide a 3D surface visualization of the SELIC Pré curve evolution, stacking 5 historical curves along a Z axis with an interpolated surface connecting adjacent curves, enabling intuitive perception of rate changes over time.

## Requirements

### Requirement: 3D evolution surface rendering
The system SHALL provide a function `render_3d_evolution(fig, date_rates, consolidated=False)` that renders a 3D surface plot using matplotlib's `plot_surface` with `mpl_toolkits.mplot3d`.

#### Scenario: Basic 3D surface renders without error
- **WHEN** `render_3d_evolution` is called with a valid figure and a dict of 5 date→records entries
- **THEN** the function returns without raising exceptions
- **AND** the figure contains a 3D subplot (`projection='3d'`)

#### Scenario: Surface uses plot_surface
- **WHEN** the 3D evolution chart is rendered
- **THEN** the chart uses `ax.plot_surface()` to draw an interpolated surface connecting adjacent curves

### Requirement: 3D view works with both detailed and consolidated data
The system SHALL support both rendering modes: raw rate data (`consolidated=False`) and yearly averages (`consolidated=True`).

#### Scenario: Consolidated mode uses yearly average data
- **WHEN** `render_3d_evolution` is called with `consolidated=True`
- **THEN** each curve's Y-values are the yearly average rates from `average_rate_by_year()`
- **AND** the X-axis represents years (0..max_year)

#### Scenario: Detailed mode uses raw rate data
- **WHEN** `render_3d_evolution` is called with `consolidated=False`
- **THEN** each curve's Y-values are the raw `rate` values from `RateRecord`
- **AND** the X-axis represents business days (Dias úteis)

### Requirement: Curves are stacked along Z axis in chronological order
The system SHALL position each curve at a distinct Z coordinate, with the most recent date at Z=0 and the oldest date at Z=4.

#### Scenario: Z=0 is the most recent date
- **WHEN** the 3D evolution chart is rendered
- **THEN** the base date (today) curve is positioned at Z=0
- **AND** the oldest curve (28 days ago) is positioned at Z=4
- **AND** intermediate dates are positioned at Z=1, Z=2, Z=3 in chronological order

### Requirement: Data interpolation for shared X grid
For detailed mode (non-consolidated), the system SHALL interpolate each curve's rate values onto a common X grid before surface rendering.

#### Scenario: Curves are interpolated to shared grid
- **WHEN** `render_3d_evolution` is called with `consolidated=False` and curves have non-identical `day252` values
- **THEN** each curve is linearly interpolated onto a common X grid spanning from 0 to the maximum `day252` across all dates
- **AND** `numpy.interp` is used with `left=np.nan` and `right=np.nan` for out-of-range values

#### Scenario: Surface handles data gaps gracefully
- **WHEN** a curve has no data beyond a certain `day252` value
- **THEN** the corresponding region of the surface contains NaN cells and does not render

### Requirement: Individual curves as black lines with decreasing linewidth
The system SHALL overlay each of the 5 curves as a black line on the surface, with linewidth decreasing from the most recent (thickest) to the oldest (thinnest).

#### Scenario: Five black lines overlaid on surface
- **WHEN** the 3D evolution chart is rendered
- **THEN** 5 black lines are plotted on top of the surface, one per date curve
- **AND** the most recent curve (Z=0) has the thickest linewidth
- **AND** the oldest curve (Z=4) has the thinnest linewidth
- **AND** intermediate curves have progressively decreasing linewidth

### Requirement: Unified colormap by rate magnitude
The system SHALL apply a single colormap to the surface where color represents the rate magnitude, not the date.

#### Scenario: Surface colored by rate value
- **WHEN** the 3D evolution chart is rendered
- **THEN** the surface uses the RdYlGn_r colormap (reversed Red-Yellow-Green) scaled to the minimum and maximum rate values across all curves
- **AND** the color at any point reflects the rate magnitude at that (X, Z) coordinate
- **AND** a colorbar is displayed alongside the chart, labeled "Taxa %"

### Requirement: Default camera angle
The system SHALL set a default 3D camera angle for optimal visualization.

#### Scenario: Default view angle is set
- **WHEN** the 3D evolution chart is rendered
- **THEN** `ax.view_init(elev=25, azim=-60)` is called to set the initial camera angle
- **AND** the user can still rotate the view using the matplotlib toolbar

### Requirement: Coordinate axes labels
The system SHALL label all three axes appropriately for the active mode.

#### Scenario: Detailed mode axes labels
- **WHEN** `render_3d_evolution` is called with `consolidated=False`
- **THEN** the X-axis is labeled "Dias úteis"
- **AND** the Y-axis is labeled "Período"
- **AND** the Z-axis is labeled "Taxa %"

#### Scenario: Consolidated mode axes labels
- **WHEN** `render_3d_evolution` is called with `consolidated=True`
- **THEN** the X-axis is labeled "Ano"
- **AND** the Y-axis is labeled "Período"
- **AND** the Z-axis is labeled "Taxa %"

### Requirement: Figure cleared before rendering
The system SHALL clear the figure before drawing the 3D subplot, following the same pattern as existing rendering functions.

#### Scenario: Figure is cleared
- **WHEN** `render_3d_evolution` is called
- **THEN** `fig.clf()` is called before creating the 3D subplot

### Requirement: X-axis limits match 2D view
The system SHALL restrict the X-axis range to match the corresponding 2D view.

#### Scenario: Detailed mode X-axis limited to 756 business days
- **WHEN** `render_3d_evolution` is called with `consolidated=False`
- **THEN** data is filtered to `day252 <= 756` before interpolation
- **AND** `ax.set_xlim(0, 756)` is called

#### Scenario: Consolidated mode X-axis limited to 20 years
- **WHEN** `render_3d_evolution` is called with `consolidated=True`
- **THEN** years are filtered to `0 <= y <= 20` before meshgrid creation
- **AND** `ax.set_xlim(0, 20)` is called

### Requirement: Y-axis labels show dates
The system SHALL label the Y (Período) axis ticks with the actual date strings.

#### Scenario: Y-axis shows date labels
- **WHEN** the 3D evolution chart is rendered
- **THEN** `ax.set_yticks(z_indices)` is called with the integer Z positions
- **AND** `ax.set_yticklabels(dates_sorted, fontsize=8)` shows date strings sorted most-recent-first

### Requirement: Smooth color gradient between curves
The system SHALL upsample the Y-axis grid so `plot_surface` produces smooth color transitions between adjacent curves.

#### Scenario: Y-axis upsampling
- **WHEN** `render_3d_evolution` is called
- **THEN** the original n×m grid is linearly interpolated to (n×20)×m rows along the Y axis
- **AND** the original curve values at Z=0..n-1 are preserved exactly
- **AND** `plot_surface` receives the upsampled grid for smoother face coloring

### Requirement: Title positioned over chart area (not colorbar)
The system SHALL shift the 3D title left to center it over the chart area.

#### Scenario: 3D title adjusted for colorbar
- **WHEN** the 3D evolution title is set
- **THEN** the title's pixel width is measured after rendering
- **AND** the title's X position is adjusted by `0.5 - 0.7 * w_ax` (70% of title width leftward)

### Requirement: Layout adjusted for 3D axes
The system SHALL use `subplots_adjust` to set appropriate margins for 3D rendering.

#### Scenario: subplots_adjust called
- **WHEN** `render_3d_evolution` renders
- **THEN** `fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)` is called

### Requirement: Empty data shows placeholder
The system SHALL handle empty or invalid data gracefully.

#### Scenario: Empty data shows placeholder
- **WHEN** `render_3d_evolution` is called with an empty `date_rates` dict
- **THEN** the chart shows "Sem dados" centered text
