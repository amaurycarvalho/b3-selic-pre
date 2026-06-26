## 1. Curve evolution chart: 1-year intervals + offset/step arrows

- [x] 1.1 Replace arrow loop: iterate over `all_years` (integer years from base date)
- [x] 1.2 Implement offset/step pattern: `trans_idx = (tick_idx - 1) % 5`, draw single arrow per tick
- [x] 1.3 Colors use `plt.cm.Blues` gradient indexed by `trans_idx`
- [x] 1.4 Run existing tests to confirm quiver is still present

## 2. Detailed evolution chart: offset/step arrows

- [x] 2.1 Implement offset/step pattern: `trans_idx = (tick_idx - 1) % 5`, draw single arrow per tick at 22 DU positions
- [x] 2.2 Colors use `plt.cm.Greens` gradient indexed by `trans_idx`
- [x] 2.3 Run existing tests to confirm quiver is still present

## 3. Visual verification

- [ ] 3.1 Launch the application and toggle curve evolution chart to visually confirm arrow layout
- [ ] 3.2 Toggle detailed evolution chart to visually confirm arrow layout
