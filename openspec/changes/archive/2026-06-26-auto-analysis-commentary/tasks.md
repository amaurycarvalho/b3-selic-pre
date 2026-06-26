# Tasks: `auto-analysis-commentary`

## Task List

- [x] **1. Adapt change artifacts to clean architecture**
  - [x] 1.1 Read current codebase structure
  - [x] 1.2 Update proposal.md paths to `src/b3_selic_pre/application/analyze/` and `src/b3_selic_pre/presentation/gui.py`
  - [x] 1.3 Update design.md example code, structure, and file references
  - [x] 1.4 Update tasks.md to reflect clean architecture

- [x] **2. Implement analysis engine: thresholds**
  - [x] 2.1 Create `_thresholds.py` with `AnalysisThresholds` dataclass
  - [x] 2.2 Define all thresholds for the 14 rules

- [x] **3. Implement analysis engine: metric extraction**
  - [x] 3.1 Create `_metrics.py` with `extract_metrics()` function
  - [x] 3.2 Implement `IndiceTendencia` calculation
  - [x] 3.3 Implement 3-segment segmentation (curto/médio/longo)
  - [x] 3.4 Implement `IndiceSuavidade` calculation
  - [x] 3.5 Implement local extrema detection
  - [x] 3.6 Implement slope change detection
  - [x] 3.7 Implement inflection point detection

- [x] **4. Implement analysis engine: rules**
  - [x] 4.1 Create `_rules.py` with `evaluate_rules()` function
  - [x] 4.2 Implement R001 (Tendência Global Ascendente)
  - [x] 4.3 Implement R002 (Tendência Global Descendente)
  - [x] 4.4 Implement R003 (Curva Plana)
  - [x] 4.5 Implement R004 (Vale)
  - [x] 4.6 Implement R005 (Pico)
  - [x] 4.7 Implement R006 (Recuperação Sustentada)
  - [x] 4.8 Implement R007 (Segmento Curto)
  - [x] 4.9 Implement R008 (Segmento Médio)
  - [x] 4.10 Implement R009 (Segmento Longo)
  - [x] 4.11 Implement R010 (Curva Suave)
  - [x] 4.12 Implement R011 (Curva Serrilhada)
  - [x] 4.13 Implement R012 (Mudança Estrutural)
  - [x] 4.14 Implement R013 (Movimento Monótono)
  - [x] 4.15 Implement R014 (Curva em Recuperação)

- [x] **5. Implement analysis engine: report**
  - [x] 5.1 Create `_report.py` with `build_report()` function
  - [x] 5.2 Implement 4-block report structure
  - [x] 5.3 Implement score classification (5 níveis)
  - [x] 5.4 Implement `format_report()` with score header

- [x] **6. Implement analysis engine: facade**
  - [x] 6.1 Update `__init__.py` facade with `analyze()` function
  - [x] 6.2 Route `raw` view mode to new rules engine
  - [x] 6.3 Return placeholder for `consolidado`/`evolucao` modes

- [x] **7. Add analysis sidebar to GUI**
  - [x] 7.1 Add `sidebar_var` (BooleanVar) and sidebar Checkbutton in bottom_frame
  - [x] 7.2 Add sidebar Text widget and Scrollbar
  - [x] 7.3 Implement `_toggle_sidebar` using grid/forget
  - [x] 7.4 Implement `_update_analysis` to fetch and display report
  - [x] 7.5 Integrate sidebar update into `_redraw_chart`
  - [x] 7.6 Remove top pady from sidebar panel frame for vertical alignment

- [x] **8. Write tests**
  - [x] 8.1 Write tests for metric extraction
  - [x] 8.2 Write tests for each rule group
  - [x] 8.3 Write tests for report generation
  - [x] 8.4 Write smoke test for facade

- [x] **9. Update pyproject.toml**
  - [x] 9.1 Add explicit numpy dependency
