## 1. Detailed chart grid (raw + detailed evolution)

- [x] 1.1 In `render_chart` raw path: set major ticks to `range(90, 757, 90)` and minor ticks to `range(1, 757, 20)` excluding multiples of 90
- [x] 1.2 In `render_detailed_evolution`: same tick configuration as 1.1
- [x] 1.3 Replace `ax.grid(True, alpha=0.3)` with split grid in both detailed functions: `ax.grid(True, which='major', alpha=0.3)` (solid) and `ax.grid(True, which='minor', alpha=0.15, linestyle='--')` (dashed)

## 2. Consolidated chart grid (yearly + consolidated evolution)

- [x] 2.1 In `render_chart` consolidated path: set major ticks to `range(0, 21, 3)` and minor ticks to `range(0, 21)` excluding multiples of 3
- [x] 2.2 In `render_curve_evolution`: same tick configuration as 2.1
- [x] 2.3 Replace `ax.grid(True, alpha=0.3)` with split grid in both consolidated functions: `ax.grid(True, which='major', alpha=0.3)` (solid) and `ax.grid(True, which='minor', alpha=0.15, linestyle='--')` (dashed)

## 3. Tests

- [x] 3.1 Run existing tests to confirm no regressions
- [x] 3.2 Update tests to verify major tick configuration (quarterly/triennial) and minor tick configuration (20-DU/annual) in each chart function
