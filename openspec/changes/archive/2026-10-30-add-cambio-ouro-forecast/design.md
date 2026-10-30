# Design

## Context

Ver `proposal.md` para motivação e `specs/` para o contrato de comportamento.

O projeto já tem os padrões que esta mudança deve reutilizar:

- `DiskCache` com TTL e housekeeping (`infrastructure/disk_cache.py`).
- Cache analítico com manifesto atômico e retenção de 3 anos (`tesouro_analytics_cache.py`, `tesouro_analytics_housekeeping.py`).
- Pré-cálculo invalidado por hash das fontes e lock dedicado (`tesouro_series_cache.py`, `tesouro_precompute.py`).
- Abas lazy com registro determinístico (`presentation/tabs.py`, `gui/shell.py`).
- MCP somente leitura, alimentado apenas por cache (`presentation/mcp/`).
- CLI como composition root, com regras de negócio em `application` (`presentation/cli.py`, `application/cli_services.py`).

Não existe hoje nenhum código de câmbio ou ouro. A spec `app-tabs` já antecipa a aba `Câmbio`, mas nenhum requisito de dados de mercado existe.

Restrições que moldam o desenho:

- Sem novas dependências: HTTP via `urllib`, gráficos com matplotlib/numpy já presentes.
- `tests/test_architecture.py` proíbe `application` de importar `presentation`, Tkinter, matplotlib ou clientes de rede.
- `tests/test_ui_test_budget.py` limita testes de UI a 5; a lógica nova deve ser testável sem display.
- `make lint` e `make complexity` exigem módulos pequenos, docstrings e complexidade controlada.
- O cache vive sob o diretório XDG já usado pela aplicação.

Resultado do spike das fontes (fonte da verdade para este desenho):

- A API antiga `arquivos.b3.com.br/apinegocios/*` retorna 404; a página UP2DATA foi desativada em 31/03/2026.
- A API nova `drp.b3.com.br/rapinegocios/ticker/{ticker}/{data}` funciona para ações e futuros DOL.
- O BDI oficial (`arquivos.b3.com.br/bdi/table/...`) expõe câmbio oficial (`HistoricalExchange`, `RTDOLD1`/`RTDOLCL`) e futuros DOL; não expõe ouro.
- `OUZ`, `OZ1D`, `OZ2D` e `OZ3D` não têm negócios; não há ouro spot/futuro oficial acessível. Só existem ETFs de ouro (`OURO11`, `GOLD11`).
- BCB SGS 1 e Focus funcionam e têm histórico longo.
- Yahoo `GC=F` entrega histórico diário de ouro (COMEX) por vários anos, mas é fonte não oficial e sujeita a rate limit.
- A awesomeapi foi removida do plano.

## Goals / Non-Goals

**Goals:**

- Entregar uma camada headless de séries, cenário e indicadores de câmbio/ouro, compartilhada por GUI, CLI e MCP.
- Garantir proveniência e defasagem visíveis em cada ponto.
- Manter a primeira exibição da sub-aba instantânea, lendo apenas cache e artefato pré-calculado.
- Invalidar o pré-cálculo somente quando a matriz de origem mudar.
- Manter o cache de mercado limitado a 3 anos.

**Non-Goals:**

- Recomendação de investimento, sinais de compra/venda ou previsão pontual.
- Dados intradiários, streaming ou websockets.
- Ouro oficial da B3 como fonte primária nesta entrega; o adapter fica preparado para troca futura.
- Curva futura de ouro da COMEX como fonte de cenário.
- Amostragem temporal por Fibonacci; Fibonacci fica restrito a níveis de preço.
- Um botão global "Atualizar tudo" ou acoplamento ao `Atualizar` da SELIC.

## Decisions

### 1. Aba de nível superior com sub-notebook, não sub-aba do Tesouro

Nova aba `Câmbio e Reservas` entre `Tesouro Direto` e `Sobre`, construída com `TabSpec` lazy e com `on_show` lendo apenas cache. Dentro dela, um sub-notebook lazy registra a sub-aba `Dólar e Ouro`, que concentra os dois painéis de preço e o botão `Atualizar` próprio.

A aba nasce como sub-notebook mesmo com uma única sub-aba para que a futura sub-aba `Reservas Internacionais` entre sem reestruturar a aba nem o shell. Cada sub-aba tem seu próprio `Atualizar`, no padrão do Tesouro Direto: o `Atualizar` de `Dólar e Ouro` não dispara a atualização de reservas, e vice-versa.

Alternativas: sub-aba dentro de `Tesouro Direto` (mistura domínios e polui a navegação) ou janela separada (contra a spec `app-tabs`).

### 2. Adaptadores de fonte com proveniência explícita

```
fonte            adapter                      saída
BCB SGS 1        BcbSgsClient                 USD/BRL oficial, diário
BCB Focus        BcbFocusClient               medianas anuais de câmbio
B3 BDI           B3MarketClient               HistoricalExchange e DOL
Yahoo GC=F       GoldUsdClient                XAU/USD diário
cache            MarketRawCache               último valor válido
```

Cada adaptador devolve `SourceRef` com `fonte`, `url`, `unidade`, `metodo`, `extraido_em`. O ouro é derivado no serviço de aplicação, não no adaptador.

Alternativas descartadas: ETF de ouro da B3 (não é o preço do metal), LBMA (bloqueado por Cloudflare), API paga (nova dependência/chave), awesomeapi (removida pelo usuário).

### 3. Derivação do ouro e fallback

```
ouro_r$/g = XAU/USD (Yahoo GC=F) * USD/BRL (BCB SGS 1) / 31,1034768
```

- A conversão de onça troy para grama fica em uma função pura testável.
- `metodo=derivado` e as duas fontes de entrada ficam no ponto.
- Se Yahoo falhar, reutiliza o último ponto válido com `metodo=cache_defasado` e `defasagem_horas`.
- Se não houver cache, o ouro fica indisponível; não há fallback de rede.
- Quando a B3 publicar ouro, basta um `B3GoldClient` produzindo o mesmo `MarketQuote`; nada mais muda.

### 4. Resolução em camadas com buckets OHLC

A série histórica é reduzida por buckets de calendário ancorados na maior data disponível:

```
|-- mensal (> 3m) --|-- semanal (15d..3m) --|-- diario (<= 14d) --| hoje
```

Cada bucket carrega `abertura`, `minimo`, `maximo`, `fechamento` e `ultimo`. O gráfico usa o fechamento para a linha e uma faixa mín-máx para mostrar amplitude. O eixo x é tempo real, não índice.

Fibonacci não entra na resolução. Ele é apenas um overlay de níveis de retração calculado sobre o mínimo/máximo da janela de 12 meses.

Alternativa descartada: amostragem por intervalos de Fibonacci. Ela perde extremos e distorce a leitura de volatilidade, justamente o que se quer detectar.

### 5. Cenário em duas trilhas

- **Dólar (mercado):** alvo = mediana Focus para o ano de referência a 12 meses; caminho mensal por interpolação log-linear do spot até o alvo; bandas a partir do desvio-padrão/min-máx do Focus. Futuros DOL entram como sinal de curto prazo, não como ajuste automático do centro na v1.
- **Ouro (estatístico):** random walk com drift encolhido e EWMA sobre retornos logarítmicos.

```
drift      = 0.5 * media(log_retornos_252d)
sigma      = EWMA(lambda=0.94, log_retornos)
centro(h)  = ultimo * exp(drift * h / 252)
banda(h)   = centro(h) * exp(+/- z * sigma * sqrt(h / 252))
z80=1.2816  z95=1.96
```

O cenário é determinístico e sempre rotulado como `cenario_mercado` ou `projecao_estatistica`.

Alternativas descartadas: usar DOL para 12 meses (só os 1-2 vencimentos front têm liquidez), usar curva de ouro da COMEX (não oficial e desnecessária), ajustar o centro do Focus pelo DOL (acopla dois sinais e dificulta explicar).

### 6. Sinais de política determinísticos

Painel separado dos preços, com:

- `premio_termo = (focus_12m / spot - 1) * 100`, anualizado.
- `premio_dol = (dol_front_ajustado / spot - 1) * 100 * 252 / dias_ate_vencimento`.
- `gap_focus = (focus_12m / spot - 1) * 100`.
- `vol30` e `vol90`: desvio-padrão anualizado dos retornos logarítmicos.
- `regime`: ligado quando `vol30/vol90 >= 1.5` e `sign(drift30) != sign(drift90)`.

O limiar fica em configuração de aplicação, com default documentado. Não há change-point estatístico na v1; a decisão é determinística e testável.

Alternativa descartada: Bayesian change-point/ruptura estrutural. Fica para uma mudança futura, depois de haver histórico acumulado.

### 7. Cache em três camadas e chave composta

```
<cache>/b3-selic-pre/market/
  raw/<fonte>/<AAAA-MM-DD>.json
  derived/<hash>/series.json
  precomputed/<hash>/artifact.json
  manifest.json
  locks/market.lock
```

`hash = sha256(fontes_ordenadas + parametros_resolucao + parametros_projecao + schema_version)`.

- `raw`: payload normalizado + metadados (`fonte`, `unidade`, `hash`, `extraido_em`, `defasado`).
- `derived`: buckets e indicadores.
- `precomputed`: artefato final consumido pela aba, CLI e MCP.
- `manifest.json`: `latest_data_date`, `sources`, `partitions`, `generated_at`.
- Escrita atômica (`write_atomic`) e lock dedicado, no padrão do cache analítico do Tesouro.
- Leitura somente de cache nunca apaga nem corrige arquivo.

TTL:

```
<= 14 dias      15-30 min (ou ate o proximo fechamento)
mes corrente    1-6 h
> 1 mes         imutavel (30-365 d ou sem TTL)
Focus           6-24 h
precomputado    por hash
```

### 8. Pré-cálculo disparado pela sub-aba, não pela SELIC

O `Atualizar` da sub-aba `Dólar e Ouro` busca as fontes, grava o `raw` e chama o pré-cálculo. Se o hash composto não mudou, o pré-cálculo retorna sem recalcular.

O `Atualizar` da SELIC não dispara o pré-cálculo de mercado: são domínios e redes diferentes, e acoplar atrasaria a carga principal. O `Atualizar` de uma sub-aba de `Câmbio e Reservas` também não dispara o pré-cálculo das outras sub-abas.

Falha no pré-cálculo preserva o artefato anterior e é registrada em log; a sub-aba continua exibindo o último artefato válido com aviso de defasagem.

### 9. Fronteiras de módulo

| Camada | Módulos novos |
|---|---|
| `domain` | `market.py`: `MarketQuote`, `MarketSeries`, `Bucket`, `ForecastPoint`, `ForecastBand`, `PolicyIndicators`, `SourceRef`, `Resolution` |
| `application` | `market/series.py`, `market/forecast.py`, `market/indicators.py`, `market/export.py`, `market/cache_key.py`, `market/payloads.py`, `market/config.py` |
| `infrastructure` | `market/bcb_client.py`, `market/b3_client.py`, `market/gold_client.py`, `market/raw_cache.py`, `market/precompute_cache.py`, `market/housekeeping.py`, `market/types.py` |
| `presentation` | `market_tab.py` (headless), `gui/market_tab.py`, `gui/market_chart_panel.py`, `charts_market.py`, `cli_commands` (handler), `mcp/tool_handlers` (handlers), catálogo |

`application` recebe adaptadores por protocolo; `infrastructure` não importa `presentation`; a GUI/CLI montam os adaptadores no composition root.

### 10. Gráficos

- Dois subplots empilhados com eixo x compartilhado: dólar em cima, ouro embaixo.
- Faixa mín-máx por bucket; linha de fechamento.
- Divisor vertical em "hoje"; região futura sombreada; cenário tracejado; bandas 80/95% em preenchimento suave.
- Alternância absoluto/base 100.
- Overlay opcional de retração de Fibonacci (23,6/38,2/50/61,8/78,6) sobre o range de 12 meses.
- Painel estreito inferior para os sinais de política.
- Renderizador só desenha; buckets, bandas e séries vêm de `application`/view-model headless.

### 11. CLI e MCP

- `mercado`: parsing em `cli_parser`, orquestração em `cli_commands`, composição em `cli.py`; a escrita de arquivo fica na apresentação.
- `--prever` gera dois artefatos; stdout só com um artefato; diretório obrigatório com múltiplos.
- MCP: 4 tools no catálogo, handlers separados, leitura exclusiva do artefato pré-calculado e do cache bruto; paginação reutiliza `application/mcp_pagination.py`.
- Nenhuma tool MCP acessa rede, escreve arquivo ou dispara atualização.

### 12. Datas, unidades e normalização

- Todas as datas são normalizadas para o calendário de `America/Sao_Paulo` antes de entrar no cache.
- `DOL` é cotado em R$ por US$ 1.000; o adaptador divide por 1.000 para obter BRL/USD.
- Ouro é armazenado em R$/g; o payload também preserva XAU/USD e USD/BRL brutos para auditoria.
- Pontos sem cotação não são interpolados silenciosamente; o gráfico usa lacuna ou último valor marcado como defasado.

### 13. Configuração

Parâmetros de projeção, limiar de regime, TTLs e retenção ficam em `application/market/config.py`, construídos a partir de mapping, sem importar `Settings`. A presentation monta a configuração e a injeta, seguindo o padrão de `CurvaJurosConfig`.

### 14. Refinamentos pós-implementação

Depois da primeira implementação, as seguintes decisões foram incorporadas e passam a fazer parte do contrato desta change:

- A aba de nível superior passa a se chamar `Câmbio e Reservas`, nome que cobre dólar, ouro e a futura sub-aba de reservas.
- A sub-aba `Dólar e Ouro` segue o padrão de usabilidade do Tesouro Direto: tooltips nos controles, toolbar vertical e cópia no gráfico, statusbar com progresso, textbox orientativo em painel lateral e `Atualizar` com ícone imediatamente à direita do combobox de ativo.
- A atualização é executada em thread de trabalho e entrega o resultado ao thread principal por fila, evitando chamadas Tkinter fora da thread principal. Falhas de atualização são exibidas na statusbar e fontes com erro são listadas no status.
- Os endpoints do BCB foram corrigidos: SGS em `/dados/serie/bcdata.sgs.{codigo}/dados` (código 1 para USD/BRL) e Focus com OData `$filter` não codificado, `$orderby=Data desc`, `$top=100` e leitura de `DataReferencia`. Sem essa correção, o `Atualizar` não capturava dólar nem expectativas Focus.
- A legenda é única, centralizada abaixo dos painéis e acima da faixa de indicadores. As faixas de legenda e indicadores foram reduzidas para ampliar proporcionalmente a área vertical dos gráficos.
- O gráfico oferece hover com data, ativo, valor, unidade e faixa mín-máx do histórico; nos pontos de cenário, inclui o valor central e as bandas de 80% e 95%.

## Risks / Trade-offs

- **Yahoo GC=F é não oficial e tem rate limit** → cache agressivo, retry com backoff, fallback para último valor em cache e badge de defasagem. O risco é aceito porque não há alternativa oficial de ouro.
- **Sem fallback de rede para ouro** → se o Yahoo falhar por muito tempo, a série fica defasada. A UI expõe idade do dado em vez de mascarar.
- **Derivação não é o ouro spot da B3** → origem `derivado` visível na tela, no CSV e no MCP.
- **Focus é anual e não mensal** → interpolação log-linear documentada; bandas usam dispersão do Focus.
- **DOL só tem liquidez no front** → usado apenas como sinal curto; o centro de 12m continua no Focus.
- **Drift do ouro pode ser instável** → encolhimento de 50% e bandas largas; o rótulo de projeção estatística evita leitura de certeza.
- **Complexidade/lint** → módulos pequenos por responsabilidade; sem classes gigantes; docstrings; sem novas dependências.
- **Orçamento de testes de UI** → toda a lógica nova é headless; testes Tkinter não são adicionados.
- **Cache pode crescer** → housekeeping de 3 anos e escrita apenas de resultados completos.
- **Falha de fonte única** → atualização parcial mantém o que existe; status identifica a fonte com falha.

## Migration Plan

- Mudança aditiva: nova aba com sub-aba `Dólar e Ouro`, novo subcomando e novas tools; nada existente é removido ou renomeado.
- O cache de mercado usa diretório novo; não há migração de cache antigo.
- Rollback: remover o registro da aba, o subcomando e as tools; o diretório de cache pode ser apagado sem afetar SELIC/Tesouro.
- Sem alteração de empacotamento ou de dependências.

## Open Questions

- Se um futuro "Atualizar tudo" deve orquestrar SELIC, Tesouro e mercado em paralelo. Fora de escopo agora.
- Se a curva de ouro da COMEX deve entrar como cenário alternativo depois de medir a utilidade do cenário estatístico. Fora de escopo agora.
