# Proposal

## Why

O aplicativo cobre SELIC Pré e Tesouro Direto, mas não oferece leitura de câmbio e ouro. Sem uma visão conjunta de histórico e cenário futuro, fica difícil perceber se o governo está mudando a política cambial. A mudança entrega uma aba dedicada com 12 meses de histórico, 12 meses de cenário e sinais de política, carregada a partir de cache local rápido.

## What Changes

- Nova aba de nível superior `Câmbio e Ouro`, lazy, organizada em sub-abas lazy; a sub-aba `Dólar e Ouro` tem botão `Atualizar` próprio e carregamento inicial apenas do cache.
- Histórico de 12 meses de dólar (BRL/USD) e ouro (R$/g), com resolução em camadas: diária nas últimas 2 semanas, semanal de 2 semanas a 3 meses e mensal acima de 3 meses, preservando mínimos e máximos por bucket.
- Cenário de 12 meses: dólar ancorado na expectativa Focus (mediana anual interpolada) com sinal de curto prazo dos futuros DOL da B3; ouro com projeção estatística (random walk com drift encolhido e volatilidade EWMA), sempre com bandas de 80% e 95% e rótulo explícito de cenário.
- Painel de sinais de política: prêmio a termo Focus versus spot, prêmio implícito curto DOL versus spot, gap Focus versus spot, volatilidade realizada 30d/90d e flag de regime determinístico.
- Fibonacci apenas como overlay de retração de preço sobre o range de 12 meses; a redução de dados vem do cache e dos buckets, não de amostragem Fibonacci.
- Fontes: BCB SGS 1 como série oficial do dólar, BCB Focus para expectativa, B3 (`HistoricalExchange` e futuros DOL) como fonte oficial complementar. Ouro em R$/g derivado de `XAU/USD (Yahoo GC=F) x USD/BRL (BCB) / 31,1034768`, com fallback para o último valor válido em cache, sem a awesomeapi. Cada ponto carrega origem, unidade, horário de extração e método (`oficial`, `derivado`, `cache_defasado`).
- Cache em camadas: bruto por fonte com TTL por recência, derivado por buckets e pré-calculado com chave de hash das fontes e parâmetros. Pré-cálculo disparado após o `Atualizar` da sub-aba, somente quando a matriz de origem mudar.
- Housekeeping com retenção de 3 anos no cache de mercado.
- Exportação via CLI no subcomando `mercado` (CSV/JSON) e tools MCP somente leitura: `mercado_serie`, `mercado_previsao`, `mercado_indicadores` e `mercado_exportar`.
- Sem novas dependências de terceiros; acesso HTTP via `urllib` existente e gráficos com matplotlib/numpy já presentes.

## Capabilities

### New Capabilities

- `cambio-ouro`: séries de dólar e ouro, derivação do ouro em R$/g, proveniência, resolução temporal, cenário de 12 meses, sinais de política e dados de gráfico.
- `market-data-cache`: cache bruto com TTL por recência, cache derivado, pré-cálculo por hash, invalidação e housekeeping de 3 anos.

### Modified Capabilities

- `app-tabs`: incluir a aba `Câmbio e Ouro` com sub-abas lazy na janela principal, mantendo construção lazy e sem rede na primeira exibição.
- `cli-interface`: adicionar o subcomando `mercado`, seus filtros, formatos CSV/JSON e regras de `--saida`.
- `mcp-tools`: adicionar as tools de mercado ao catálogo somente leitura, com paginação e erros de domínio.

## Impact

- Novos módulos em `domain`, `application`, `infrastructure` e `presentation`, respeitando as fronteiras de camada e o composition root da CLI/GUI.
- Nova aba com sub-notebook no shell, novo subcomando na CLI, novas tools no catálogo MCP e novos diretórios de cache sob o cache XDG da aplicação.
- Testes headless para séries, cenário, indicadores, cache e payloads; nenhum aumento do orçamento de testes de UI.
- Nenhuma mudança destrutiva nas abas, comandos ou tools existentes.
