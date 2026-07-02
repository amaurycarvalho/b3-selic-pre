# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3.

## Interface gráfica

Dois modos base selecionáveis por radio button, com opção adicional de evolução:

| Modo                    | Descrição                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Detalhado**           | Curva completa Dias úteis × taxa (linha verde), com grid trimestral (~66 DU) e ticks finos a cada ~22 DU                                                                                    |
| **Consolidado**         | Envelope anual consolidado (taxa mínima em azul, máxima em vermelho), com grid trienal (3 anos) e ticks finos a cada ano                                                                    |
| **Evolução da curva** ☐ | Checkbox que sobrepõe 5 curvas históricas (hoje, 7, 14, 21, 28 dias atrás) com gradiente de cor e flechas quiver nos ticks secundários (~22 DU / ~1 ano), combinável com qualquer modo base |
| **3D** ☐                | Checkbox que renderiza a evolução como superfície 3D (plot_surface com colormap RdYlGn_r), disponível apenas quando "Evolução da curva" está ativo; compatível com Detalhado e Consolidado |
| **Análise** ☐           | Checkbox que exibe um sidebar à direita com dois sub-paineis de análise textual: "Resumo Executivo — Curva Atual" (nível) e "Evolução da Curva" (delta, se modo Evolução ativo)          |

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.
Use o botão `📅` ao lado do campo de data para abrir um calendário popup.

**Limite de consulta**: nos modos Detalhado e Consolidado, apenas datas nos últimos 30 dias corridos são aceitas.

**Evolução da curva**: ao marcar o checkbox, a data é automaticamente alterada para a data atual. O sistema busca as 5 curvas (28, 21, 14, 7, 0 dias atrás) em paralelo e as sobrepõe ao gráfico do modo base ativo. Quando **Análise** também está ativo, o sidebar passa a exibir o sub-painel "Resumo Executivo — Evolução da Curva" com os deltas entre a curva atual e a imediatamente anterior.

Recursos disponíveis:

- Zoom e pan no gráfico
- Cópia de dados para área de transferência
- Cópia do gráfico como imagem
- Exportação do gráfico em PNG
- Criação de atalho no desktop (botão "Criar Atalho Desktop" ou `--create-shortcut`)
- Painel de análise textual (sidebar) com indicadores de nível e evolução

## Painel de Análise (sidebar)

Ao marcar **Análise** ☐, um sidebar é exibido à direita com dois sub-paineis:

### Resumo Executivo — Curva Atual

Fotografia do mercado: mostra os indicadores de **nível** calculados a partir da curva carregada.

| Bloco | Descrição |
|---|---|
| **Nível Nominal** | Classificação da taxa curta em 5 faixas (Muito Baixos a Muito Altos) |
| **Política Monetária** | Juro real e classificação em 4 faixas (Expansionista a Muito Restritiva) |
| **Inclinação** | Diferença entre taxa longa e curta em bps, classificada em 5 faixas (Quase Plana a Muito Inclinada) |
| **Prêmio de Prazo** | Inclinação classificada em 5 faixas (Muito Baixo a Muito Elevado) |
| **Estabilidade das Expectativas** | Desvio médio da inclinação nas últimas N curvas (Alta/Média/Baixa) |
| **Última Mudança** | Variação da inclinação (Steepening/Flattening/Estável) |
| **Mensagem do Mercado** | Síntese em linguagem natural |

### Resumo Executivo — Evolução da Curva

**Filme** do mercado: calcula os **deltas** entre a curva atual e a anterior, mostrado apenas quando o modo **Evolução da curva** está ativo e há curva anterior disponível. Os dois painéis são separados por uma linha divisória horizontal.

| Bloco | Descrição |
|---|---|
| **Regime** | Classificação composta (ex: Bear Steepening, Bull Flattening, Twist, Estável) combinando movimento (Bear/Bull/Twist) e inclinação (Steepening/Flattening/Parallel Shift) |
| **Política Monetária** | ΔJuro Real em bps com seta direcional ▲/▼/→ e texto descritivo |
| **Prêmio de Prazo** | ΔInclinação em bps com seta direcional ▲/▼/→ e texto descritivo |
| **Intensidade** | Magnitude do movimento em 5 faixas (Muito Fraca a Muito Forte) |
| **Direção Geral** | Indicador derivado (ex: ↑ Revisão Altista, ↓ Revisão Baixista, → Estável) |
| **Mensagem do Mercado** | Síntese em linguagem natural |

Quando o regime é **Estável** (abaixo do threshold de movimento), apenas Regime, Direção Geral e Mensagem do Mercado são exibidos (versão compacta de 3 blocos).

## Indicadores e cálculos envolvidos

### Curva Atual (nível)

| Indicador | Fórmula / Fonte |
|---|---|
| **Taxa curta** | Primeiro vértice da curva (D1) |
| **Taxa longa** | Último vértice da curva (D~N~) |
| **Inclinação** | (TaxaLonga − TaxaCurta) × 100 bps |
| **Juro real** | TaxaCurta − InflaçãoEsperada |
| **Nível Nominal** | Taxa curta classificada em faixas configuráveis |
| **Política Monetária** | Juro real classificado em faixas configuráveis |
| **Prêmio de Prazo** | Inclinação classificada em bps |
| **Estabilidade** | Desvio médio da inclinação nas últimas N curvas |
| **Steepening** | ΔInclinação entre curva atual e anterior |

### Evolução da Curva (delta)

| Etapa | Função | Descrição |
|---|---|---|
| **1. Extrair deltas** | `extrair_deltas()` | ΔCurto = (Curto~atual~ − Curto~ant~) × 100 bps; ΔLongo = (Longo~atual~ − Longo~ant~) × 100 bps; ΔSlope = Inclinação~atual~ − Inclinação~ant~; ΔReal = ΔCurto (inflação fixa) |
| **2. Movimento** | `classificar_movimento()` | Bear (ambos sobem), Bull (ambos caem), Twist (movimento oposto), Estável (\|Δ\| < threshold) |
| **3. Inclinação** | `classificar_slope_movement()` | Steepening (ΔSlope > threshold), Flattening (ΔSlope < −threshold), Parallel Shift |
| **4. Regime** | `classificar_regime()` | Combinação: Bear/Bull + Steepening/Flattening/Parallel Shift, Twist ou Estável |
| **5. Intensidade** | `classificar_intensidade()` | max(\|ΔCurto\|, \|ΔLongo\|) em 5 faixas: Muito Fraca (≤5), Fraca (5-15), Moderada (15-30), Forte (30-50), Muito Forte (>50 bps) |
| **6. ΔPolítica Monetária** | `classificar_politica_monetaria()` | ΔReal em 5 faixas: muito mais restritiva (>20), ligeiramente (+5 a +20), neutra (\|Δ\| ≤5), ligeiramente menos (−5 a −20), muito menos (<−20 bps) |
| **7. ΔPrêmio de Prazo** | `classificar_premio_prazo()` | ΔSlope em 5 faixas: aumentou significativamente (>20), aumentou (10-20), estável (\|Δ\| ≤10), diminuiu (−10 a −20), forte redução (<−20 bps) |
| **8. Direção Geral** | `derivar_direcao_geral()` | 6 regras combinando regime + intensidade: ↑ Revisão Altista, ↓ Revisão Baixista, ↕ Misto, → Estável |
| **9. Texto** | `gerar_texto_*()` / `montar_evolucao_resumo()` | Geração de linguagem natural para cada bloco + mensagem final |
| **10. Orquestração** | `analyze_evolution()` | Pipeline completo: deltas → classificações → texto → `EvolutionReport` |

## Parametrizações

Configurações salvas em `~/.config/b3-selic-pre/settings.json`.

### curva_juros

| Parâmetro | Default | Descrição |
|---|---|---|
| `expected_inflation` | `3.0` | Inflação esperada (%) para cálculo do juro real |
| `faixas_nominais` | `[6.0, 9.0, 11.0, 13.0]` | Limites das faixas de classificação nominal |
| `faixas_juro_real` | `[2.0, 4.0, 6.0]` | Limites das faixas de classificação do juro real |
| `stability_window` | `4` | Número de curvas históricas para calcular estabilidade |
| `stability_fallback` | `"default"` | Comportamento quando não há histórico suficiente |
| `faixas_estabilidade` | `[5.0, 10.0, 20.0, 35.0]` | Limites das faixas de estabilidade (bps) |

### curva_evolucao

| Parâmetro | Default | Descrição |
|---|---|---|
| `movement_threshold_bps` | `5.0` | Threshold mínimo para classificar movimento como Bear/Bull/Twist (abaixo disso → Estável) |
| `steepening_threshold_bps` | `5.0` | Threshold mínimo para classificar inclinação como Steepening/Flattening |
| `very_weak_max` | `5.0` | Limite superior da faixa "Muito Fraca" (bps) |
| `weak_max` | `15.0` | Limite superior da faixa "Fraca" (bps) |
| `moderate_max` | `30.0` | Limite superior da faixa "Moderada" (bps) |
| `strong_max` | `50.0` | Limite superior da faixa "Forte" (bps) |
| `highly_restrictive_min` | `20.0` | ΔReal mínimo para "Mercado passou a precificar política mais restritiva" (bps) |
| `slightly_restrictive_min` | `5.0` | ΔReal mínimo para "Política ligeiramente mais restritiva" (bps) |
| `neutral_max` | `5.0` | \|ΔReal\| máximo para "Política praticamente inalterada" (bps) |
| `slightly_loose_max` | `20.0` | ΔReal mínimo (negativo) para "Política ligeiramente menos restritiva" (bps) |
| `significantly_increased_min` | `20.0` | ΔSlope mínimo para "Prêmio de prazo aumentou significativamente" (bps) |
| `increased_min` | `10.0` | ΔSlope mínimo para "Prêmio aumentou" (bps) |
| `decreased_min` | `20.0` | ΔSlope mínimo (negativo) para "Forte redução do prêmio" (bps) |

Os parâmetros `steepening_fallback`, `estimated_delta_slope_bps`, `steepening_small_bps`, `steepening_medium_bps` e `steepening_large_bps` também podem ser configurados sob `curva_evolucao` para controle do steepening do painel "Curva Atual".
