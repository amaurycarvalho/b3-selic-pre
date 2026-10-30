# Proposal

## Why

O sistema trata apenas fins de semana como não úteis. Feriados são tentados como datas de carga e exibidos como se fossem dias de negociação: a janela de evolução pode consultar a B3 em feriado, o cache do Tesouro se considera vencido em feriado e os "últimos dias úteis" usados por TTL e por status ficam errados. As changes `add-cambio-ouro-forecast` e `add-reservas-cambiais` dependem de "último dia útil", "5 dias úteis" e distinção entre lacuna esperada e dado faltando, então o calendário precisa existir antes delas serem implementadas.

## What Changes

- Novo calendário interno de feriados, alimentado pela ANBIMA (`feriados/fer_nacionais/{ano}.asp`), com fallback para o cache anterior e, sem cache algum, para a regra de fim de semana com estado degradado explícito.
- Cache por ano com TTL por recência, cache negativo para ano futuro ainda não publicado e housekeeping de 3 anos em `[ano_atual - 3, ano_atual + 1]`.
- Resolução de data não útil passa a retroceder para o dia útil anterior e a avisar: barra de status na GUI, `stderr` na CLI e campos explícitos no payload MCP.
- Atualização do calendário junto das cargas existentes, antes de resolver a data, com lock e TTL; falha de fonte nunca bloqueia a carga.
- Janela de evolução mantém `EVOLUTION_DAYS = [28, 21, 14, 7, 0]`, mas cada alvo não útil retrocede para o dia útil anterior; a data-base já resolvida é preservada.
- "Último dia útil" de TTL e de status do Tesouro passa a considerar feriados, não só fins de semana.
- Exportação na CLI em `b3-selic-pre feriados` (CSV/JSON, por ano) e consulta de uma data.
- Tools MCP somente leitura e alimentadas apenas por cache: `feriados_listar`, `feriados_consultar` e `feriados_exportar`.
- Nova aba de nível superior `Feriados`, lazy, entre `Câmbio e Ouro` e `Sobre`, com árvore de anos, meses e dias à esquerda e textbox somente leitura à direita; a árvore mostra o dia da semana abreviado entre parênteses e o texto também mostra o dia da semana.
- Botão de atualização na aba `Feriados` com o mesmo ícone `view-refresh`/`content-loading` das sub-abas do Tesouro Direto, forçando a revalidação do calendário e preservando o cache anterior em caso de falha.
- Ajuste do tooltip da evolução de "últimos 7 pregões" para "últimos 5 pregões", coerente com as 5 datas já carregadas.

## Capabilities

### New Capabilities

- `calendario-feriados`: fonte ANBIMA, normalização, cache por ano com TTL e housekeeping, fallback para cache anterior, resolução de dia útil com motivo e proveniência, payloads de consulta/exportação e aba `Feriados` com árvore ano/mês/dia e textbox somente leitura.

### Modified Capabilities

- `app-tabs`: registrar a aba de nível superior `Feriados` entre `Câmbio e Ouro` e `Sobre`, mantendo construção lazy e sem rede na primeira exibição.
- `b3-rate-source`: não solicitar datas não úteis para a data-base e para a janela de evolução.
- `curve-evolution`: alvos da janela ajustados para o dia útil anterior, mantendo os cinco pontos e deduplicando por data.
- `desktop-rate-browser`: data inicial no último dia útil, aviso de ajuste na barra de status e uso do calendário na busca histórica.
- `cli-interface`: subcomando `feriados`, consulta de data e aviso de ajuste em `stderr`.
- `mcp-tools`: tools de feriados e campos de ajuste nos payloads existentes, todas somente cache.
- `tooltips`: tooltip da evolução passa a informar os últimos 5 pregões.
- `tesouro-direto`: TTL e frescor do cache passam a usar o último dia útil calendário-aware.
- `tesouro-analise`: TTL dos recursos do Tesouro passa a usar o último dia útil calendário-aware.
- `tesouro-resgates`: TTL de recompras passa a usar o último dia útil calendário-aware.
- `market-data-cache`: recência por último dia útil e data esperada do artefato passam a considerar feriados.
- `cambio-ouro`: validação de lacunas por dia útil e status de defasagem passam a distinguir feriado de dado faltante.
- `reservas-cambiais`: sobreposição de 5 dias úteis e status de última data esperada passam a usar o calendário.

## Impact

- Novos módulos em `domain` (`calendar.py`), `application` (`calendar/`), `infrastructure` (`calendar/`) e `presentation` (CLI `feriados`, handlers MCP, aba `Feriados` e ajustes de GUI), respeitando as fronteiras de camada.
- Nova aba no shell, com `ttk.Treeview` à esquerda e textbox somente leitura à direita, registrada no notebook principal sem reestruturar o shell.
- Novo namespace de cache sob o cache XDG da aplicação, com lock e housekeeping próprios.
- Chamadas de atualização nas cargas existentes (SELIC, Tesouro e, quando implementadas, mercado e reservas), sempre best-effort.
- Mudança de comportamento nas datas da janela de evolução, nos payloads MCP e nos avisos da CLI/GUI.
- Nenhuma dependência de terceiros nova; parsing da ANBIMA com a biblioteca padrão.
- Depende de `add-cambio-ouro-forecast` e `add-reservas-cambiais` implementadas e arquivadas antes de aplicar os deltas de `market-data-cache`, `cambio-ouro` e `reservas-cambiais`.
- Testes headless para fonte, cache, resolução, janela, CLI e MCP; nenhum aumento do orçamento de testes de UI.
