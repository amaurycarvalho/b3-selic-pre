# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-10-30

### [add-btd-estoque-overlay](openspec/changes/archive/2026-10-30-add-btd-estoque-overlay/) Spike realizado em 2026-10-30: o dataset CKAN `estoque-do-tesouro-direto` tinha a maior data em `2026-08` (metadados atualizados em 2026-10-16), enquanto o Balanço do Tesouro Direto (BTD) de setembro já estava publicado em 2026-10-29 com o estoque de `2026-09`.

#### Added

- Novo adaptador da publicação BTD: descobre a edição mais recente na página de publicações, localiza o anexo XLSX e lê a aba `2.1 - Estoque por Título`.
- Normalização do estoque por título/mês/valor do BTD para um modelo agregado, com cache próprio, gravação atômica e TTL curto (publicação mensal, mas revalidada diariamente).
- Política de sobreposição: ao atualizar a sub-aba `Estoque`, meses do BTD posteriores ao maior mês do CKAN são acrescentados; meses já existentes no CKAN NÃO SHALL ser substituídos.
- Leitura offline do cache BTD junto do cache CKAN, sem rede na primeira exibição.
- A série analítica de estoque e a data-base passam a considerar o mês mais recente do CKAN ou do BTD, e a invalidação do cache analítico considera o hash da sobreposição.
- O status da sub-aba `Estoque` distingue quando a fonte complementar BTD contribuiu com um mês mais recente.
- O dataset CKAN, o modelo detalhado (`vencimento`, `PU`, `quantidade`), a CLI `tesouro-estoque` e os demais consumidores de estoque permanecem inalterados.

#### Changed

- Falha do BTD NÃO SHALL falhar o refresh do CKAN; a sub-aba continua com os dados anteriores e informa a indisponibilidade de forma não bloqueante.

### [add-calendario-feriados](openspec/changes/archive/2026-10-30-add-calendario-feriados/) O sistema trata apenas fins de semana como não úteis.

#### Added

- Novo calendário interno de feriados, alimentado pela ANBIMA (`feriados/fer_nacionais/{ano}.asp`), com fallback para o cache anterior e, sem cache algum, para a regra de fim de semana com estado degradado explícito.
- Cache por ano com TTL por recência, cache negativo para ano futuro ainda não publicado e housekeeping de 3 anos em `[ano_atual - 3, ano_atual + 1]`.
- Exportação na CLI em `b3-selic-pre feriados` (CSV/JSON, por ano) e consulta de uma data.
- Tools MCP somente leitura e alimentadas apenas por cache: `feriados_listar`, `feriados_consultar` e `feriados_exportar`.
- Nova aba de nível superior `Feriados`, lazy, entre `Câmbio e Ouro` e `Sobre`, com árvore de anos, meses e dias à esquerda e textbox somente leitura à direita; a árvore mostra o dia da semana abreviado entre parênteses e o texto também mostra o dia da semana.
- Botão de atualização na aba `Feriados` com o mesmo ícone `view-refresh`/`content-loading` das sub-abas do Tesouro Direto, forçando a revalidação do calendário e preservando o cache anterior em caso de falha.

#### Changed

- Resolução de data não útil passa a retroceder para o dia útil anterior e a avisar: barra de status na GUI, `stderr` na CLI e campos explícitos no payload MCP.
- Atualização do calendário junto das cargas existentes, antes de resolver a data, com lock e TTL; falha de fonte nunca bloqueia a carga.
- Janela de evolução mantém `EVOLUTION_DAYS = [28, 21, 14, 7, 0]`, mas cada alvo não útil retrocede para o dia útil anterior; a data-base já resolvida é preservada.
- "Último dia útil" de TTL e de status do Tesouro passa a considerar feriados, não só fins de semana.
- Ajuste do tooltip da evolução de "últimos 7 pregões" para "últimos 5 pregões", coerente com as 5 datas já carregadas.

### [add-cambio-ouro-forecast](openspec/changes/archive/2026-10-30-add-cambio-ouro-forecast/) O aplicativo cobre SELIC Pré e Tesouro Direto, mas não oferece leitura de câmbio e ouro.

#### Added

- Nova aba de nível superior `Câmbio e Reservas`, lazy, organizada em sub-abas lazy; a sub-aba `Dólar e Ouro` tem botão `Atualizar` próprio e carregamento inicial apenas do cache.
- Histórico de 12 meses de dólar (BRL/USD) e ouro (R$/g), com resolução em camadas: diária nas últimas 2 semanas, semanal de 2 semanas a 3 meses e mensal acima de 3 meses, preservando mínimos e máximos por bucket.
- Cenário de 12 meses: dólar ancorado na expectativa Focus (mediana anual interpolada) com sinal de curto prazo dos futuros DOL da B3; ouro com projeção estatística (random walk com drift encolhido e volatilidade EWMA), sempre com bandas de 80% e 95% e rótulo explícito de cenário.
- Painel de sinais de política: prêmio a termo Focus versus spot, prêmio implícito curto DOL versus spot, gap Focus versus spot, volatilidade realizada 30d/90d e flag de regime determinístico.
- Fontes: BCB SGS 1 como série oficial do dólar, BCB Focus para expectativa, B3 (`HistoricalExchange` e futuros DOL) como fonte oficial complementar. Ouro em R$/g derivado de `XAU/USD (Yahoo GC=F) x USD/BRL (BCB) / 31,1034768`, com fallback para o último valor válido em cache, sem a awesomeapi. Cada ponto carrega origem, unidade, horário de extração e método (`oficial`, `derivado`, `cache_defasado`).
- Cache em camadas: bruto por fonte com TTL por recência, derivado por buckets e pré-calculado com chave de hash das fontes e parâmetros. Pré-cálculo disparado após o `Atualizar` da sub-aba, somente quando a matriz de origem mudar.
- Housekeeping com retenção de 3 anos no cache de mercado.
- Exportação via CLI no subcomando `mercado` (CSV/JSON) e tools MCP somente leitura: `mercado_serie`, `mercado_previsao`, `mercado_indicadores` e `mercado_exportar`.

#### Changed

- Fibonacci apenas como overlay de retração de preço sobre o range de 12 meses; a redução de dados vem do cache e dos buckets, não de amostragem Fibonacci.
- Sem novas dependências de terceiros; acesso HTTP via `urllib` existente e gráficos com matplotlib/numpy já presentes.
- Refinamentos pós-implementação: aba renomeada para `Câmbio e Reservas`; sub-aba `Dólar e Ouro` alinhada ao padrão do Tesouro Direto (tooltips, toolbar do gráfico, statusbar, texto orientativo e `Atualizar` com ícone ao lado do combobox); endpoints do BCB corrigidos; atualização thread-safe com erro visível no status; legenda centralizada abaixo dos painéis, com mais área vertical para os gráficos; hover com data, ativo, valor, unidade, faixa mín-máx e bandas do cenário.

### [add-reservas-cambiais](openspec/changes/archive/2026-10-30-add-reservas-cambiais/) O aplicativo acompanha SELIC Pré e Tesouro Direto, e a change `add-cambio-ouro-forecast` trará a leitura de câmbio e ouro.

#### Added

- Nova sub-aba `Reservas Internacionais` dentro da aba `Câmbio e Ouro`, lazy, com `Atualizar` próprio e carregamento inicial apenas do cache.
- Série diária do BCB SGS 13621 (reservas internacionais, conceito de liquidez, US$ milhões), com janela padrão de 12 meses e opção de 3 anos.
- Cache reutilizando o core de `add-cambio-ouro-forecast`: snapshot bruto normalizado por fonte, hash canônico dos pares `(data, valor)`, busca incremental com overlap de revisões, TTL por recência e escrita atômica.
- Housekeeping de 3 anos ancorado na maior data disponível, com o hash calculado sobre a janela retida para a limpeza não invalidar o pré-cálculo.
- Indicadores determinísticos de direção: nível atual, variações de 1/3/12 meses, tendência de 90 dias, drawdown de 12 meses, posição na faixa de 12 meses e regime `aumento | estavel | deterioracao`, com limiares configuráveis.
- Gráfico de linha/área com seletor de janela, médias móveis, selo de regime e proveniência/defasagem.
- Exportação via CLI no subcomando `reservas` (CSV/JSON) e tools MCP somente leitura: `reservas_serie`, `reservas_indicadores` e `reservas_exportar`.

#### Changed

- Pré-cálculo invalidado pelo hash da matriz de origem e pelos parâmetros, disparado pelo `Atualizar` da sub-aba; falha preserva o artefato anterior.
- Reuso das estruturas de `add-cambio-ouro-forecast` (`BcbSgsClient`, `SourceRef`, `MarketSeries`, `Bucket`, precompute, housekeeping e regras de `--saida`), sem novas dependências de terceiros.

### [fix-tesouro-status-feedback](openspec/changes/archive/2026-10-30-fix-tesouro-status-feedback/) A statusbar das sub-abas do Tesouro Direto mistura estados incompatíveis.

#### Changed

- Priorizar o estado de carregamento sobre erro antigo e sobre a orientação de cache vazio na statusbar e no texto centralizado dos gráficos.
- Limpar o erro anterior no início de cada carga, para que uma nova tentativa mostre progresso em vez da falha antiga.
- Reavaliar a disponibilidade de cache a cada exibição da sub-aba, permitindo que dados gravados por outra sub-aba sejam reconhecidos sem reiniciar o aplicativo.
- Distinguir na statusbar a leitura de cache da atualização de rede, informando a etapa corrente (`vendas`, `resgates`, `estoque`) durante o refresh.
- Manter a barra de progresso indeterminada e a desabilitação dos controles conforme o contrato atual, sem adicionar progresso determinado ao Tesouro.

#### Fixed

- Tratar falha inesperada de leitura de cache como aviso explícito, em vez de reportá-la como ausência de dados.

### [improve-gui-loading-feedback](openspec/changes/archive/2026-10-30-improve-gui-loading-feedback/) A montagem e o desenho dos gráficos do Tesouro Direto levam tempo perceptível.

#### Added

- Adicionar um texto fixo `Processando as informações. Aguarde…` atrás dos gráficos do Tesouro Direto.
- Adicionar ao início do `README.md` uma seção com o resumo das funcionalidades e replicar o mesmo texto na aba Sobre.

#### Changed

- Ao selecionar uma sub-aba, ocultar temporariamente os gráficos para que o texto fixo apareça; reexibi-los somente após a carga de dados e o desenho concluírem.
- Ao acionar `Atualizar`, ocultar os gráficos enquanto a atualização processa e reexibi-los somente após a carga de dados completar.
- Manter o ponteiro de espera `watch`, a statusbar e o progresso durante o processamento.
- Na troca de janela de análise, manter os gráficos visíveis e usar apenas o ponteiro de espera.
- Estabilizar a geometria para que ocultar/reexibir os gráficos e a barra de progresso não desloque o conteúdo.
- Centralizar a aplicação de `tight_layout` em um helper que captura o aviso, registra-o no log com o contexto do gráfico e aplica margens conservadoras de fallback.
- Renomear a aba de nível superior de `Câmbio e Ouro` para `Câmbio e Reserva` no shell, no README e na aba Sobre.
- Aplicar às sub-abas `Dólar e Ouro` e `Reservas Internacionais` o mesmo texto fixo atrás do gráfico, ocultação durante a carga e reexibição após o desenho usados no Tesouro Direto.
- Estabilizar a geometria das sub-abas de câmbio e reservas com host fixo de progresso e rótulos de status estáveis.
- Não alterar cache, clientes HTTP, payloads nem o orçamento de testes de UI.

### [log-gui-refresh-failures](openspec/changes/archive/2026-10-30-log-gui-refresh-failures/) Falhas de leitura de cache, de atualização e de fontes parciais nas sub-abas de dados da interface gráfica são hoje apenas convertidas em texto de status ou descartadas.

#### Added

- Adicionar uma consulta pública `was_logged` em `presentation/logging_utils.py` para evitar registro duplicado da mesma exceção.
- Registrar falhas de leitura de cache e de atualização das sub-abas do Tesouro Direto, identificando a sub-aba e a operação.
- Registrar a falha tolerada de resgates do Tesouro sem interromper a atualização.
- Registrar falhas de fonte, pré-cálculo e housekeeping das Reservas Internacionais sem interromper a atualização.
- Registrar cada fonte de mercado que falhou e as falhas de pré-cálculo/housekeeping, mantendo `erros_fontes` e os dados disponíveis.
- Registrar nos workers da GUI apenas exceções que escapam do controller, usando `was_logged` para não duplicar.

#### Changed

- Manter a classificação existente: falhas de comunicação em uma linha, sem traceback; defeitos inesperados com traceback.
- Não alterar comportamento visual, cache, TTL, clientes HTTP nem payloads.

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.2.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
