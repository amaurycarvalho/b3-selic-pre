# Tasks

## 1. Domain: calendário puro

- [x] 1.1 Criar `domain/calendar.py` com `Holiday` e `HolidayCalendar` (fim de semana, feriados, `is_business_day`, `previous_business_day`, `next_business_day`, `business_days_between`); verificar com testes unitários de dia útil, sábado, domingo e feriado.
- [x] 1.2 Cobrir blocos de feriados consecutivos e virada de ano nos testes; verificar que o retrocesso atravessa o bloco até o primeiro dia útil anterior.

## 2. Application: serviço e portas

- [x] 2.1 Criar `application/calendar/ports.py` com os protocolos `HolidaySource` e `HolidayRepository`; verificar que nenhuma implementação concreta é importada pela camada.
- [x] 2.2 Criar `application/calendar/service.py` com `BusinessDayResolution`, `ensure_year`, `resolve_business_day` e `evolution_targets`; verificar com testes de motivo `fim_de_semana`, motivo `feriado`, nome do feriado e data preservada.
- [x] 2.3 Criar `application/calendar/config.py` com TTLs, retenção e sobreposição padrão lidos de mapping; verificar defaults e override por teste headless.

## 3. Infrastructure: fonte ANBIMA

- [x] 3.1 Implementar o cliente HTML da ANBIMA com a biblioteca padrão, normalizando `d/m/aa` para ISO e validando o dia da semana; verificar com fixtures de 2024, 2025 e 2026 sem rede.
- [x] 3.2 Classificar 404, página inesperada, timeout e HTML inválido como falha de fonte, sem gravar calendário parcial; verificar com testes de cada caso.
- [x] 3.3 Verificar fechamentos específicos da B3 fora da lista da ANBIMA (candidatos: 24/12 e 31/12) e, se confirmados, adicionar complemento explícito no adaptador; verificar com teste do complemento.

## 4. Infrastructure: cache e housekeeping

- [x] 4.1 Implementar cache por ano com leitura/gravação atômica e lock dedicado; verificar com teste de escrita concorrente e leitura somente cache.
- [x] 4.2 Implementar TTL por recência (passado imutável, corrente curto, futuro curto) e cache negativo de ano não publicado; verificar com testes de cache fresco, vencido e negativo.
- [x] 4.3 Implementar a cadeia de fallback (cache fresco, ANBIMA, cache anterior defasado, fim de semana degradado); verificar cada ramo com testes.
- [x] 4.4 Implementar housekeeping de `[ano_corrente - 3, ano_corrente + 1]`; verificar remoção de 2021, preservação de 2023–2027 e tolerância a arquivo corrompido.

## 5. Integração com as cargas existentes

- [x] 5.1 Garantir o calendário antes de resolver a data em `consultar` e `atualizar`; verificar com teste que a chamada de `ensure_year` antecede a resolução.
- [x] 5.2 Adicionar o hook nas cargas do Tesouro; verificar com teste que a falha do calendário não falha o refresh.
- [x] 5.3 Adicionar o hook no `mcp --atualizar`; verificar com teste de preparação que o calendário é garantido antes do cache de taxas.
- [x] 5.4 Registrar falha do calendário em log sem bloquear a carga; verificar com teste de exceção da fonte.

## 6. Resolução calendário-aware nas superfícies

- [x] 6.1 Substituir `nearest_business_day` pela resolução do serviço em `cli_data`, `gui/fetch` e `gui/chart`; verificar com testes de feriado e fim de semana nos três pontos.
- [x] 6.2 Emitir aviso em `stderr` na CLI com data solicitada, data resolvida e motivo; verificar com teste de saída.
- [x] 6.3 Incluir `data_solicitada`, `data_resolvida`, `ajustada` e `motivo` nos payloads MCP que aceitam data; verificar com testes de data útil e data ajustada.
- [x] 6.4 Ajustar a data inicial da GUI e o aviso na barra de status; verificar com teste headless de construção e de mensagem.

## 7. Janela de evolução (Opção A)

- [x] 7.1 Alterar `evolution_dates(base, calendar)` para resolver cada alvo e deduplicar por data; verificar com teste de alvo em feriado e de alvos duplicados.
- [x] 7.2 Injetar o calendário em `b3_client.fetch_historical_rates` e `cached_client`; verificar com teste de que nenhuma requisição é feita para feriado.
- [x] 7.3 Atualizar o tooltip de "últimos 7 pregões" para "últimos 5 pregões"; verificar com teste de texto e com `openspec validate`.

## 8. Tesouro: último dia útil no TTL

- [x] 8.1 Delegar `_last_business_day` ao calendário com fallback para fim de semana; verificar com testes de feriado e de calendário indisponível.
- [x] 8.2 Ajustar `is_current` e `ttl_for` para não considerar o cache vencido em feriado; verificar com teste de cache do dia útil anterior.

## 9. CLI: subcomando feriados

- [x] 9.1 Adicionar `feriados` ao parser com `--ano`, `--data`, `--formato`, `--saida` e `--atualizar`; verificar com teste de ajuda e de argumentos inválidos.
- [x] 9.2 Implementar listagem e consulta de data a partir do cache; verificar com testes de ano com cache, data útil e data feriado.
- [x] 9.3 Implementar exportação CSV e JSON com as regras de `--saida`; verificar com testes de stdout, arquivo e diretório.
- [x] 9.4 Atualizar a ajuda da CLI e a documentação de comandos; verificar executando os comandos documentados.

## 10. GUI: aba Feriados

- [x] 10.1 Criar `presentation/feriados_view_model.py` com a árvore headless ano/mês/dia e os textos de ano, mês e dia; verificar com testes de ordem decrescente de anos, meses só com feriados, rótulo `DD (abrev)` e agrupamento por mês.
- [x] 10.2 Criar `presentation/gui/feriados_tab.py` com `ttk.Treeview` à esquerda e textbox somente leitura à direita; verificar com teste headless que a construção lê apenas cache, não acessa rede e respeita o orçamento de testes de UI.
- [x] 10.3 Ligar a seleção da árvore aos textos de ano, mês e dia, incluindo o dia da semana ao lado do dia; verificar com testes do view-model para cada nível de seleção.
- [x] 10.4 Implementar o botão de atualização com `icons['view-refresh']`, troca para `content-loading` durante a carga, desabilitação do botão e `ensure_year(..., force=True)` em thread separada, atualizando o ano corrente quando a árvore estiver vazia; verificar com teste de controlador que o cache anterior é preservado em falha e a seleção é mantida em sucesso.
- [x] 10.5 Registrar a aba `Feriados` no shell entre `Câmbio e Ouro` e `Sobre`; verificar com teste do registro de abas e com `openspec validate`.
- [x] 10.6 Adicionar tooltip ao botão de atualização e à árvore; verificar com teste de texto e sem aumentar o orçamento de UI.

## 11. MCP: tools de feriados

- [x] 11.1 Adicionar `feriados_listar`, `feriados_consultar` e `feriados_exportar` ao catálogo e aos handlers; verificar com teste de catálogo e de schema.
- [x] 11.2 Garantir leitura somente cache, sem rede e sem escrita de arquivo; verificar com teste que a fonte não é chamada.
- [x] 11.3 Implementar paginação e erro `sem_dados` com dica acionável; verificar com testes de cursor, fim de página e ano ausente.

## 12. Mercado e reservas (após as changes dependentes)

- [x] 12.1 Aplicar "último dia útil" calendário-aware no TTL do cache de mercado; verificar com teste de feriado sem revalidação.
- [x] 12.2 Comparar a maior data do artefato com o último dia útil esperado; verificar com testes de artefato em dia e defasado.
- [x] 12.3 Usar o calendário na sobreposição de 5 dias úteis das reservas; verificar com teste de sobreposição atravessando feriado.
- [x] 12.4 Classificar lacunas de câmbio/ouro como esperadas em feriado e reais em dia útil; verificar com testes dos dois casos.

## 13. Validação final

- [x] 13.1 Executar `make lint`; verificar que termina sem erros.
- [x] 13.2 Executar `make complexity`; verificar que termina sem violações.
- [x] 13.3 Executar `make test`; verificar a suíte completa, porque a resolução de data é compartilhada por GUI, CLI e MCP.
- [x] 13.4 Teste manual opcional: abrir a GUI em um feriado e confirmar data ajustada, aviso na barra de status e janela de evolução sem requisição na data do feriado.
- [x] 13.5 Teste manual opcional: abrir a aba `Feriados`, conferir ano/mês/dia com dia da semana, clicar em atualizar e confirmar o ícone de carga e a preservação do conteúdo em caso de falha.

## Workflow follow-up

- Aplicar e arquivar `add-cambio-ouro-forecast` e `add-reservas-cambiais` antes de implementar o grupo 12 e de arquivar esta change.
- Arquivar esta change somente depois que os deltas de `market-data-cache`, `cambio-ouro` e `reservas-cambiais` encontrarem as specs principais.
