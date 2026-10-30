# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-10-30

### [add-tesouro-analise-percentuais](openspec/changes/archive/2026-10-30-add-tesouro-analise-percentuais/) As changes `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` entregam dados brutos de vendas, resgates e estoque, mas o objetivo analítico do produto é responder, em percentual, **qual a composição do estoque por indexador** (SELIC, IPCA, Prefixado, IGP-M) e **qual o apetite do mercado por título**. Sem uma camada derivada, esses números só existem se o usuário somar e normalizar manualmente os CSVs.

#### Added

- Adicionar a capability `tesouro-analise` para classificar títulos por família de indexador e calcular percentuais normalizados.
- Classificar `Tesouro Reserva` como SELIC (subfamília `SELIC_RESERVA`, somada em SELIC no headline).
- Calcular composição do estoque por valor: `% = valor_estoque(família/título) / valor_estoque(total do mês)`.
- Calcular apetite do mercado por valor: `% = valor(vendas) / valor(total da janela)`, com janelas de 14 dias, 3 meses, 12 meses e 3 anos.
- Calcular fluxo líquido por título/família: vendas menos recompras antecipadas; vencimentos e cupons ficam fora do apetite.
- Oferecer séries temporais normalizadas por família, produto e produto+vencimento, com buckets diário, semanal e mensal.
- Adicionar cache analítico em `.../b3-selic-pre/tesouro/analytics/`, com retenção de 3 anos e housekeeping ancorado no `latest_data_date`.
- Manter o cache bruto cumulativo completo; aplicar TTL condicional: 1 h para vendas/recompras quando o cache contém o dia corrente, 6 h para histórico, 24 h para estoque/cupom/vencimentos.
- Adicionar health check da fonte de estoque: validar dataset, recurso CSV, cabeçalho e mês consolidado; falhar com `TesouroDataError` se a fonte mudar ou sumir.
- Expor uma API headless de séries (`SeriesPoint`/`SeriesProvider`) reutilizável pela futura change de câmbio.

### [add-tesouro-analytics-precompute](openspec/changes/archive/2026-10-30-add-tesouro-analytics-precompute/) A primeira exibição das sub-abas de `Tesouro Direto` ainda lê e reprocessa os CSVs brutos: o parse de vendas e resgates chega a ~15 s e a montagem dos gráficos de 3 anos a ~7 s. O cache analítico já existe em `infrastructure/tesouro_analytics_cache.py`, mas não tem consumidor em `src/`; a GUI atual contradiz a spec `tesouro-analise-gui`, que exige leitura apenas do cache analítico na primeira exibição.

#### Added

- Pré-calcular séries normalizadas por fonte (`estoque`, `demanda` de vendas e `fluxo` de vendas menos resgates) após uma atualização bem-sucedida, de forma automática e fora da thread da UI.
- Guardar as séries no cache analítico existente, com escrita atômica, lock dedicado e retenção de 3 anos.
- Invalidar e recalcular apenas a fonte cujo CSV bruto mudou (`sha256`); resposta `304` ou conteúdo idêntico não reprocessa nada.
- Reutilizar os registros já parseados pelo refresh e agregar em uma passada em lote, sem reler o CSV logo em seguida.
- Fazer a GUI ler as séries pré-calculadas na primeira exibição e ao trocar de janela, sem parse de CSV e sem rede.
- Quando só houver cache bruto, montar as séries uma vez em background e persistir, preservando o comportamento atual sem exigir novo download.
- Manter o cache bruto e os comandos CLI atuais inalterados.

### [add-tesouro-direto-resgates-estoque](openspec/changes/archive/2026-10-30-add-tesouro-direto-resgates-estoque/) Adicionar a consulta de resgates (recompras, cupom e vencimentos) e do estoque mensal do Tesouro Direto à CLI e ao servidor MCP

#### Added

- Adicionar os subcomandos `tesouro-resgates` e `tesouro-estoque`, com filtros por tipo, título e período, agregação, saída CSV/JSON e exportação via `--saida`.
- Adicionar os modelos `ResgateTesouroDireto` e `EstoqueTesouroDireto`.
- Adicionar parsing por recurso: recompras sem `PU`, cupom/vencimentos com `PU` e estoque mensal com `Mes Estoque` e `Valor Estoque`.
- Adicionar filtros, agregação e ordenação de resgates e estoque, incluindo `PU` ponderado e proibição de somar estoque entre meses.
- Generalizar a descoberta CKAN e o cache para múltiplos recursos, com CSV e metadata independentes.
- Selecionar o cupom mais novo por `last_modified` e isolar falhas por recurso.
- Aplicar TTL de 1 h/6 h para recompras corrente/histórico e 24 h para cupom, vencimentos e estoque.
- Adicionar as tools MCP somente leitura `tesouro_resgates` e `tesouro_estoque`, com filtros, agregação, paginação e `cache_vazio`.
- Atualizar a documentação da CLI, do MCP, das fontes de dados e o README.

### [add-tesouro-direto-vendas](openspec/changes/archive/2026-10-30-add-tesouro-direto-vendas/) Adicionar a consulta de vendas do Tesouro Direto à CLI e à GUI, com schema confirmado e cache cumulativo

#### Added

- Adicionar o subcomando `tesouro`, com filtros por título/período, agregação por título, saída CSV/JSON e exportação via `--saida`.
- Adicionar o modelo `VendaTesouroDireto` e o processamento headless de parsing, filtros, agregação e formatação.
- Adicionar descoberta CKAN, download condicional (`ETag`/`Last-Modified`/`304`), retry transitório e validação de corpo parcial.
- Adicionar cache cumulativo atômico em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/`, com TTL de 1 h para dado corrente e 6 h para histórico.
- Adicionar a tool MCP somente leitura `tesouro_vendas`, com filtros, agregação, paginação e erro `cache_vazio`.
- Atualizar a documentação da CLI, do MCP, das fontes de dados, o README, o PRD e o RFC-001.

### [add-tesouro-gui](openspec/changes/archive/2026-10-30-add-tesouro-gui/) A aplicação hoje é uma janela única com a curva SELIC Pré. As changes de Tesouro Direto planejam uma janela separada (`Toplevel`) com tabelas, o que fragmenta a experiência e não acomoda a evolução futura para câmbio. O produto precisa de uma **janela única com abas por classe de ativo** e, dentro de Tesouro Direto, sub-abas de análise (estoque e apetite) com gráficos, não mais uma janela concorrente.

#### Added

- Introduzir um shell de abas de nível superior com `SELIC Pré`, `Tesouro Direto` e o ponto de extensão para `Câmbio` (registrada na change futura).
- Manter `SELIC Pré` como a tela atual, inalterada, agora dentro de uma aba; ela permanece a aba padrão.
- Adicionar a aba `Tesouro Direto` com as sub-abas `Visão geral`, `Estoque` e `Apetite do mercado`.
- Em cada sub-aba, exibir dois gráficos: **percentual atual** e **evolução**, com seletor de janela 14d/3m/12m/3a. Na `Visão geral`, o gráfico atual compara estoque e apetite, e o de evolução mostra o gap entre eles.
- Carregar o conteúdo das sub-abas de forma lazy, na primeira vez que ficarem visíveis; abas ocultas NÃO SHALL ser construídas no startup.
- Ao exibir uma sub-aba pela primeira vez, ler apenas o cache analítico; se não houver cache, orientar “clique em Atualizar”, sem download automático.
- Oferecer “Atualizar” e “Ignorar cache” por sub-aba, com progresso indeterminado e status próprio.
- Refinar o chrome das sub-abas: botão de atualizar apenas com ícone, tooltips, statusbar com progresso, separadores, toolbar de gráfico com cópia, rótulos de hover e painel redimensionável com texto orientativo.
- Exibir a legenda do gráfico SELIC Pré sempre no canto superior direito.
- Adicionar a aba de nível superior `Sobre`, à direita de `Tesouro Direto`, replicando o conteúdo e as funcionalidades do botão `Sobre` da aba SELIC Pré; o botão existente permanece.
- Manter o título atual da janela até a change de Câmbio.

#### Removed

- Remover do escopo das changes de vendas/resgates a janela `Toplevel` e as abas de tabelas; as tabelas brutas continuam apenas na CLI.

### [move-tesouro-evolution-legend-top-left](openspec/changes/archive/2026-10-30-move-tesouro-evolution-legend-top-left/) Nos gráficos temporais das sub-abas de `Tesouro Direto`, a legenda fica no canto superior direito, sobre o fim da série, que é justamente onde estão os dados mais recentes. Posicioná-la no início da série libera essa área e acompanha a direção de leitura do eixo do tempo.

#### Added

- Adicionar verificação de que os gráficos temporais usam a legenda no canto superior esquerdo.

#### Changed

- Mover a legenda dos gráficos temporais (evolução de `Estoque`/`Apetite do mercado` e gap da `Visão geral`) para o canto superior esquerdo.
- Manter inalterada a posição da legenda dos gráficos de percentual atual.

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.1.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
