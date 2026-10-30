# Design

## Context

Ver `proposal.md` para motivação e `specs/` para o contrato de comportamento.

Estado atual que molda o desenho:

- `application/use_cases.py:75` resolve dia útil olhando apenas `weekday() >= 5`.
- `infrastructure/tesouro_cache.py:49` faz a mesma coisa para decidir frescor e TTL.
- `application/use_cases.py:92` gera a janela de evolução com offsets de calendário `[28, 21, 14, 7, 0]`; como a base já foi ajustada, os alvos herdam o mesmo dia da semana e só feriados escapam.
- `presentation/gui/selic_pre_tab.py:113` inicia a data com o dia corrente cru.
- `presentation/cli_data.py:21`, `presentation/gui/fetch.py:44`, `presentation/gui/chart.py:110` e `presentation/mcp/tool_inputs.py` chamam a resolução de data.
- `infrastructure/b3_client.py` e `infrastructure/cached_client.py` recebem a base já resolvida, mas calculam os alvos internamente.
- O cache do Tesouro usa TTL condicional com "último dia útil"; o cache de mercado e o de reservas, quando implementados, também.

Spike da fonte (fonte da verdade para este desenho):

- A ANBIMA publica `feriados/fer_nacionais/{ano}.asp`, em ISO-8859-1, com uma tabela `Data | Dia da Semana | Feriado` e datas `d/m/aa`.
- A página cobre 2001–2099 e inclui Carnaval e Corpus Christi, que são os dias sem negociação relevantes para o app.
- O `feriados_nacionais.xls` também existe, mas é BIFF antigo e exigiria `xlrd`; não vale a dependência.
- Não há API JSON pública estável do governo. A decisão é ANBIMA como fonte única, com fallback para o cache anterior.

Restrições de projeto:

- `application` não importa `presentation`, Tkinter, matplotlib nem rede.
- `domain` não importa I/O, `json`, `pathlib` nem `urllib`.
- Testes de UI não podem aumentar o orçamento; a lógica nova é headless.
- `make lint` e `make complexity` exigem módulos pequenos e complexidade controlada.
- O app não ganha dependências de terceiros.

## Goals / Non-Goals

**Goals:**

- Centralizar a definição de dia útil em uma camada headless reutilizada por GUI, CLI, MCP e caches.
- Evitar requisições e exibições em feriados sem tornar a ANBIMA um ponto de falha da carga principal.
- Manter o calendário barato, com cache por ano, TTL por recência e retenção de 3 anos.
- Tornar o ajuste de data visível em todas as superfícies.
- Oferecer uma aba `Feriados` para consulta visual por ano, mês e dia, com atualização forçada.

**Non-Goals:**

- Calendário de feriados estaduais ou municipais.
- Substituir o calendário de negociação oficial da B3; a ANBIMA é a fonte escolhida e diferenças pontuais ficam como item de verificação.
- Mudar a contagem de 5 datas da janela de evolução.
- Adicionar uma segunda fonte de rede para feriados.
- Permitir edição manual ou inclusão de feriados pela GUI.

## Decisions

### 1. ANBIMA como fonte única, com fallback em cadeia

```
cache do ano dentro do TTL       -> usa
cache vencido/ausente + rede     -> ANBIMA
ANBIMA falhou                    -> cache anterior do ano, marcado defasado
sem cache algum                  -> fim de semana apenas + calendario_indisponivel
```

O adaptador vive em `infrastructure/calendar/source.py`, baixa a página do ano, extrai apenas as linhas da tabela e devolve `Holiday` normalizado. A escolha por HTML em vez do XLS evita `xlrd`. A escolha por fonte única evita dois formatos e mantém a semântica previsível.

Alternativas descartadas: BrasilAPI (comunidade, não é calendário de mercado), XLS da ANBIMA (dependência nova), B3/BCB (sem feed público estável no spike), segunda fonte de rede (complexidade sem ganho).

### 2. Cache por ano com TTL por recência e cache negativo

```
<cache>/b3-selic-pre/calendar/
  holidays/2023.json ... 2027.json
  locks/calendar.lock
```

Cada arquivo carrega `schema_version`, `year`, `source`, `source_url`, `fetched_at`, `ttl_seconds`, `published` e `holidays[{date, weekday, name}]`.

```
ano passado      imutavel
ano corrente     TTL curto (24h a 7d)
ano futuro       TTL curto + cache negativo quando ainda nao publicado
```

O cache negativo evita consultar a ANBIMA a cada carga enquanto o próximo ano não existe. A escrita é atômica (`write_atomic`) e o lock é dedicado, no padrão do cache analítico do Tesouro.

### 3. Housekeeping de 3 anos

A retenção é `[ano_corrente - 3, ano_corrente + 1]`. O limite inferior é 3 porque uma janela de 3 anos ancorada em outubro de 2026 começa em outubro de 2023, então o arquivo de 2023 ainda é necessário. O limite superior cobre o próximo ano para resolução de datas futuras próximas.

O housekeeping roda após uma atualização bem-sucedida, com o mesmo lock, e nunca remove o ano que a operação corrente está usando. Arquivos corrompidos são ignorados.

Alternativa descartada: reter exatamente 3 arquivos; quebraria a janela de reservas na virada de ano.

### 4. Resolução de dia útil com motivo, separada da apresentação

`domain/calendar.py` contém a regra pura:

```
Holiday(date, name)
HolidayCalendar(holidays, weekend={5,6})
  is_business_day(d)
  previous_business_day(d)
  next_business_day(d)
  business_days_between(a, b)
```

`application/calendar/service.py` devolve uma resolução estruturada:

```
BusinessDayResolution:
  data_solicitada
  data_resolvida
  ajustada
  motivo            fim_de_semana | feriado | null
  feriado           nome ou null
  calendario_estado ok | defasado | indisponivel
```

A presentation formata: barra de status na GUI, `stderr` na CLI e campos no payload MCP. A regra não fica duplicada em cada superfície.

### 5. Janela de evolução com Opção A

A base é resolvida antes de tudo. Para cada offset de `EVOLUTION_DAYS`, o alvo é resolvido para o dia útil anterior quando necessário. Duplicatas são colapsadas pelo próprio `dict` de `historical_data`.

```
base = resolve_business_day(data_pedida)
alvos = [resolve_business_day(base - 28d), ..., resolve_business_day(base)]
```

Mantém os 5 pontos na prática e evita qualquer requisição em feriado. O custo aceito é o espaçamento irregular quando um alvo é ajustado. Alternativa B (5 pregões) foi descartada para não mudar a semântica da janela nem os rótulos existentes.

### 6. Injeção do calendário e composição

`evolution_dates(base_date, calendar)` passa a receber o calendário. Os composition roots (GUI, CLI, MCP) constroem o serviço e o injetam:

- `b3_client.fetch_historical_rates` recebe o calendário (ou a lista de datas já resolvida) do composition root;
- `cached_client` usa o mesmo calendário;
- `mcp/tool_inputs.load_historical` usa o mesmo calendário;
- a GUI usa o mesmo serviço na data inicial, no `Buscar` e no `Hoje`.

Não há calendário global implícito, para evitar estado escondido e cache velho.

### 7. Atualização antes da resolução, best-effort

```
acao de carga
   -> calendar.ensure(year)      # cache fresco? usa : ANBIMA : cache anterior
   -> resolve_business_day(data) # com aviso
   -> carrega dados
```

`ensure` usa lock, TTL e timeout curto. Falha não bloqueia a carga. Isso garante que a primeira carga de um feriado não tente a data errada.

Gatilhos: `consultar`, `atualizar`, Tesouro, futuro `mercado`/`reservas` e `mcp --atualizar`. `exportar` e tools MCP não disparam rede; usam somente cache.

### 8. "Último dia útil" calendário-aware nos TTLs e status

- `tesouro_cache._last_business_day` passa a delegar para o calendário; sem calendário, fim de semana.
- `tesouro_cache.is_current` e `ttl_for` usam essa definição.
- O cache de mercado e o de reservas usam a mesma definição para recência e para `latest_data_date` esperado.
- O hash de pré-cálculo não inclui o calendário, porque feriados não alteram valores da série.

### 9. Fronteiras de módulo

| Camada | Módulos |
|---|---|
| `domain` | `calendar.py`: `Holiday`, `HolidayCalendar` |
| `application` | `calendar/ports.py`, `calendar/service.py`, `calendar/config.py` |
| `infrastructure` | `calendar/source.py`, `calendar/cache.py`, `calendar/housekeeping.py` |
| `presentation` | `feriados_view_model.py` (árvore e textos headless), `gui/feriados_tab.py` (widgets), handlers CLI de `feriados`, handlers MCP, formatação de aviso, ajustes em `cli_data`, `gui/fetch`, `gui/chart`, `mcp/tool_inputs` |

`application` recebe `HolidaySource` e `HolidayRepository` por protocolo; `infrastructure` implementa. A presentation monta os adaptadores.

### 10. Superfícies de consulta e exportação

CLI:

```
b3-selic-pre feriados
  --ano AAAA            --data AAAA-MM-DD
  --formato csv|json    --saida CAMINHO
  --atualizar
```

MCP:

- `feriados_listar` (ano, cursor, limite)
- `feriados_consultar` (data)
- `feriados_exportar` (ano, formato)

Todas somente leitura e somente cache, com erro `sem_dados` quando o ano não estiver no cache.

### 11. Aba Feriados no shell

A aba `Feriados` é registrada no notebook principal entre `Câmbio e Ouro` e `Sobre`, com `TabSpec` lazy. A primeira exibição lê apenas o cache e monta a árvore; nenhuma rede é acessada na construção.

```
+--------------------------------------------------------------+
| [view-refresh]  Calendario de feriados        status/source  |
+----------------------+---------------------------------------+
| Treeview             | Textbox readonly                      |
| 2026                 | 2026                                  |
|   01 - Janeiro       |   Janeiro                             |
|     01 (qui)         |     01 (qui) - Confraternizacao...    |
|   02 - Fevereiro     |   Fevereiro                           |
|     16 (seg)         |     16 (seg) - Carnaval               |
|     17 (ter)         |     17 (ter) - Carnaval               |
| 2025                 |                                       |
+----------------------+---------------------------------------+
```

- Anos em ordem decrescente, apenas anos presentes no cache dentro da retenção; meses apenas com feriados, em ordem crescente; dias em ordem crescente.
- Folha de dia com rótulo `DD (abrev)`, usando `dom`, `seg`, `ter`, `qua`, `qui`, `sex`, `sáb`.
- Ao selecionar ano, mês ou dia, o textbox somente leitura mostra a lista correspondente, sempre com o dia da semana ao lado do dia.
- A árvore e os textos são construídos por um view-model headless (`feriados_view_model.py`), testável sem Tk; `gui/feriados_tab.py` só desenha e liga eventos.
- O botão de atualização reutiliza `icons['view-refresh']` e troca para `icons['content-loading']` durante a operação, no mesmo padrão de `tesouro_sub_tab_ui.py`. Ele força `ensure_year(..., force=True)` para os anos exibidos (ou para o ano corrente quando a árvore está vazia), roda em thread separada e reabilita os controles ao final.
- Sucesso reconstrói a árvore e tenta preservar a seleção anterior; falha mantém a árvore e o texto atuais, marca defasagem e informa a barra de status.
- Sem cache, a árvore fica vazia e o textbox orienta a usar o botão de atualização.
- Nenhum teste de UI novo é necessário: a árvore, os rótulos e os textos são cobertos por testes headless. Se um teste Tk for indispensável, ele precisa caber no orçamento atual.

## Risks / Trade-offs

- **HTML da ANBIMA pode mudar** → parser tolerante, fixtures de 2024/2025/2026, validação do dia da semana e falha explícita sem calendário parcial.
- **Calendário bancário difere do calendário da B3** → item de verificação para fechamentos específicos (candidato: 24/12 e 31/12); se confirmado, um complemento explícito de recessos entra no adaptador, não na regra.
- **Primeira carga de um feriado antes do cache** → `ensure` roda antes da resolução; falha cai para fim de semana e marca degradado.
- **Ajuste silencioso em CLI/MCP** → contrato estruturado com `data_solicitada`, `data_resolvida` e `motivo` em todas as superfícies.
- **Espaçamento irregular na Opção A** → datas reais aparecem no eixo e na legenda; a análise usa as datas ordenadas e `stability_window = 4`.
- **Housekeeping de 3 anos pode remover ano ainda usado** → nunca remove o ano da operação corrente e roda sob o mesmo lock.
- **Cache negativo de ano futuro** → TTL curto para não atrasar a publicação.
- **Falha de rede recorrente** → cache anterior marcado defasado; a carga principal nunca depende do calendário.
- **Complexidade/lint** → módulos pequenos por responsabilidade, docstrings, sem novas dependências.
- **Orçamento de testes de UI** → toda a lógica é headless; nenhum teste Tkinter novo.

## Migration Plan

- Change aditiva: novo namespace de cache, novo subcomando, novas tools e ajustes de comportamento.
- Ordem obrigatória: aplicar e arquivar `add-cambio-ouro-forecast` e `add-reservas-cambiais` antes dos deltas de `market-data-cache`, `cambio-ouro` e `reservas-cambiais`. A validação já avisa que esses deltas só arquivam depois.
- Não há migração de cache antigo: o calendário começa vazio e é preenchido na primeira carga.
- Rollback: remover o registro do subcomando, as tools, a aba `Feriados` e os hooks; o diretório `calendar/` pode ser apagado sem afetar SELIC, Tesouro, dólar ou reservas.
- Sem alteração de empacotamento ou dependências.

## Open Questions

- Se a B3 tem fechamentos próprios fora da lista da ANBIMA (por exemplo, véspera de Natal e de Ano-Novo). Confirmar no spike da implementação; se houver, entram como complemento explícito do adaptador.
