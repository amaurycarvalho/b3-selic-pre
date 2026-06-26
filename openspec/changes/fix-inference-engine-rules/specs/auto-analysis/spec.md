## MODIFIED Requirements

### Requirement: Metric extraction from detailed rate data
The system SHALL extract quantitative metrics from a list of `RateRecord` objects for use in rule evaluation. Metrics SHALL include: initial rate, final rate, maximum rate, minimum rate, **index of the global minimum rate (`indice_minimo_global`)**, standard deviation of successive rate differences (suavidade), and count of direction changes (oscillations).

#### Scenario: Metrics computed from valid records
- **WHEN** the system receives a non-empty list of RateRecord objects
- **THEN** all metrics are computed deterministically using numpy operations
- **AND** `indice_minimo_global` SHALL contain the 0-based index where the minimum rate first occurs

#### Scenario: Empty records produce zero/None metrics
- **WHEN** the system receives an empty list
- **THEN** all metrics SHALL return safe defaults (0.0, None, or empty)

### Requirement: R004 Vale detection
The system SHALL detect a valley (vale) shape when: (a) exactly 1 local minimum exists; (b) the position of that minimum relative to the total number of points is below `vale_posicao_max` (default 0.35); and (c) `taxa_final > taxa_inicial`. The position ratio SHALL be calculated as `indice_do_minimo / total_de_pontos` using the 0-based index of the minimum in the rates array.

#### Scenario: Vale detected
- **WHEN** a curve has exactly 1 local minimum at index 5 out of 38 points (ratio 0.13 < 0.35) and `taxa_final > taxa_inicial`
- **THEN** R004 activates with inference `CURVA_COM_VALE`, score +1, text mentioning "depressão na parte curta"

#### Scenario: Vale not detected — minimum too far
- **WHEN** a curve has exactly 1 local minimum at index 20 out of 38 points (ratio 0.53 >= 0.35)
- **THEN** R004 does NOT activate

### Requirement: R005 Pico detection
The system SHALL detect a peak (pico) shape when: (a) exactly 1 local maximum exists; and (b) after the peak position, at least 80% of successive rate deltas (point-to-point differences) are negative, indicating sustained decline.

#### Scenario: Pico detected with sustained decline
- **WHEN** a curve has exactly 1 local maximum at index 3 and at least 80% of `np.diff(rates[3:])` are negative
- **THEN** R005 activates with inference `CURVA_COM_PICO`, score +1, text mentioning "pico na parte inicial"

#### Scenario: Pico not detected — no sustained decline
- **WHEN** a curve has exactly 1 local maximum but fewer than 80% of post-peak deltas are negative
- **THEN** R005 does NOT activate

### Requirement: R006 Recuperação Sustentada detection
The system SHALL detect sustained recovery when, after the global minimum position (`indice_minimo_global`), at least 80% of successive rate deltas (point-to-point `np.diff` from that position onward) are positive.

#### Scenario: Sustained recovery detected
- **WHEN** the global minimum is at index 5 and at least 80% of `np.diff(rates[5:])` are positive
- **THEN** R006 activates with inference `RECUPERACAO_SUSTENTADA`, score +1

#### Scenario: Sustained recovery not detected
- **WHEN** the global minimum is at index 5 but fewer than 80% of post-minimum deltas are positive
- **THEN** R006 does NOT activate

### Requirement: R010 Curva Suave detection
The system SHALL detect a smooth curve when the relative suavidade index (`indice_suavidade / amplitude`) is below or equal to `suavidade_relativo` threshold (default 0.01). If `amplitude == 0` (perfectly flat curve), the curve SHALL be considered smooth by definition.

#### Scenario: Smooth curve detected
- **WHEN** `indice_suavidade = 0.02` and `amplitude = 4.0` (ratio 0.005 <= 0.01)
- **THEN** R010 activates with inference `CURVA_SUAVE`, score +1

#### Scenario: Smooth curve not detected — high relative roughness
- **WHEN** `indice_suavidade = 0.08` and `amplitude = 1.0` (ratio 0.08 > 0.01)
- **THEN** R010 does NOT activate

#### Scenario: Flat curve is smooth by definition
- **WHEN** `amplitude == 0` (all rates equal)
- **THEN** R010 activates regardless of `indice_suavidade` value

### Requirement: R013 Movimento Monótono detection
The system SHALL detect monotonic movement when at least `monotonico_ratio` (default 0.90, i.e., 90%) of successive rate deltas across the entire curve (`np.diff(rates)`) share the same sign (all positive or all negative).

#### Scenario: Monotonic ascending curve
- **WHEN** at least 90% of `np.diff(rates)` are positive
- **THEN** R013 activates with inference `MOVIMENTO_MONOTONO`, score 0

#### Scenario: Non-monotonic curve
- **WHEN** fewer than 90% of `np.diff(rates)` share the same sign
- **THEN** R013 does NOT activate

### Requirement: Aggregate score computation with direction-aware classification
The system SHALL compute an aggregate score by summing weights of all activated rules. The score classification SHALL depend on the global trend direction determined by which trend rule activated (R001 ascendente, R002 descendente, or R003 plana).

Classification labels by score range and direction:

| Score | Ascendente (R001)                    | Descendente (R002)                   | Plana (R003)           |
|-------|--------------------------------------|--------------------------------------|------------------------|
| 0–2   | Mercado estável                      | Mercado estável                      | Mercado estável        |
| 3–4   | Mudança moderada                     | Mudança moderada                     | Mudança moderada       |
| 5–7   | Curva estruturalmente ascendente     | Curva estruturalmente invertida      | Curva estruturada      |
| 8–10  | Reprecificação ascendente relevante  | Reprecificação descendente relevante | Reprecificação relevante|
| 11+   | Mudança estrutural asc. expressiva   | Mudança estrutural desc. expressiva  | Mudança estrutural expressiva |

#### Scenario: Ascending curve with high score
- **WHEN** R001 activated and score is 6
- **THEN** classification SHALL be "Curva estruturalmente ascendente"

#### Scenario: Descending curve with high score
- **WHEN** R002 activated and score is 6
- **THEN** classification SHALL be "Curva estruturalmente invertida"

#### Scenario: Flat curve with low score
- **WHEN** R003 activated and score is 1
- **THEN** classification SHALL be "Mercado estável"

## ADDED Requirements

### Requirement: R015 Oscilação Elevada detection
The system SHALL detect elevated oscillation when the ratio of direction changes (`qtd_mudancas`) to total points exceeds `oscilacao_ratio` threshold (default 0.30). Direction changes are counted as sign changes in successive rate differences.

#### Scenario: Elevated oscillation detected
- **WHEN** `qtd_mudancas / total_points >= 0.30`
- **THEN** R015 activates with inference `CURVA_OSCILANTE`, score -1, text "Existem diversas oscilações locais, sugerindo baixa uniformidade da curva."

#### Scenario: Low oscillation — rule not activated
- **WHEN** `qtd_mudancas / total_points < 0.30`
- **THEN** R015 does NOT activate

### Requirement: R016 Amplitude Reduzida detection
The system SHALL detect reduced amplitude when the total curve spread (`amplitude`) is below `amplitude_reduzida` threshold (default 0.10), indicating strong market consensus.

#### Scenario: Reduced amplitude detected
- **WHEN** `amplitude < 0.10`
- **THEN** R016 activates with inference `AMPLITUDE_REDUZIDA`, score 0, text "A amplitude reduzida da curva indica forte consenso do mercado sobre o nível das taxas."

#### Scenario: Normal amplitude — rule not activated
- **WHEN** `amplitude >= 0.10`
- **THEN** R016 does NOT activate

### Requirement: R017 Amplitude Elevada detection
The system SHALL detect elevated amplitude when the total curve spread (`amplitude`) exceeds `amplitude_elevada` threshold (default 1.50), indicating significant market dispersion.

#### Scenario: Elevated amplitude detected
- **WHEN** `amplitude > 1.50`
- **THEN** R017 activates with inference `AMPLITUDE_ELEVADA`, score +1, text "A amplitude elevada da curva sugere dispersão significativa nas expectativas de mercado."

#### Scenario: Normal amplitude — rule not activated
- **WHEN** `amplitude <= 1.50`
- **THEN** R017 does NOT activate

### Requirement: R018 Curva Invertida detection
The system SHALL detect a twisted/inverted curve when the short segment delta is positive (rising) above `delta_segmento_relevante` AND the long segment delta is negative (falling) below `-delta_segmento_relevante`, configuring a structural twist regardless of global trend.

#### Scenario: Twisted curve detected
- **WHEN** `curto.delta > +0.10` AND `longo.delta < -0.10`
- **THEN** R018 activates with inference `CURVA_TORCIDA`, score +2, text mentioning "torção na estrutura a termo"

#### Scenario: Not twisted — both segments rising
- **WHEN** `curto.delta > +0.10` AND `longo.delta > 0`
- **THEN** R018 does NOT activate

### Requirement: R019 Achamento/Empinamento detection
The system SHALL detect flattening or steepening between curve segments when both short and long deltas share the same sign but differ in magnitude by a factor of at least `steepening_ratio` (default 2.0).

- Achamento (flattening): `curto.delta > longo.delta * steepening_ratio`, both positive or both negative.
- Empinamento (steepening): `longo.delta > curto.delta * steepening_ratio`, both positive or both negative.

#### Scenario: Flattening detected
- **WHEN** `curto.delta = +0.30` and `longo.delta = +0.10` (both positive, curto 3x > longo)
- **THEN** R019 activates with inference `ACHATAMENTO_ESTRUTURAL`, score +1

#### Scenario: Steepening detected
- **WHEN** `curto.delta = +0.05` and `longo.delta = +0.20` (both positive, longo 4x > curto)
- **THEN** R019 activates with inference `EMPINAMENTO_ESTRUTURAL`, score +1

#### Scenario: Similar segment deltas — rule not activated
- **WHEN** `curto.delta = +0.15` and `longo.delta = +0.12` (ratio 1.25 < 2.0)
- **THEN** R019 does NOT activate

### Requirement: R020 Formato-S detection
The system SHALL detect an S-shaped curve when the number of inflection points (`qtd_inflexoes`) is 2 or more, indicating multiple curvature changes.

#### Scenario: S-shaped curve detected
- **WHEN** `qtd_inflexoes >= 2`
- **THEN** R020 activates with inference `FORMATO_S`, score +1, text mentioning "formato sigmoide na estrutura a termo"

#### Scenario: Single or no inflection — rule not activated
- **WHEN** `qtd_inflexoes < 2`
- **THEN** R020 does NOT activate
