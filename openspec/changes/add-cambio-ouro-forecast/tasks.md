# Tasks

## 1. Domínio e serviços de aplicação

- [ ] 1.1 Criar os modelos puros de mercado (`MarketQuote`, `MarketSeries`, `Bucket`, `ForecastPoint`, `ForecastBand`, `PolicyIndicators`, `SourceRef`, `Resolution`) em `domain/market.py` e validar com testes de igualdade, unidades e datas
- [ ] 1.2 Criar a configuração de mercado e a chave composta de cache em `application/market/config.py` e `application/market/cache_key.py`, verificando com testes de hash estável, ordem das fontes e mudança de parâmetros
- [ ] 1.3 Implementar o bucketing em camadas (diário, semanal, mensal) com OHLC em `application/market/series.py` e verificar com testes de borda (14 dias, 3 meses, virada de mês, feriado ausente)
- [ ] 1.4 Implementar a derivação do ouro em R$/g e a conversão onça/grama em `application/market/series.py`, verificando com testes de precisão, origem `derivado` e fallback `cache_defasado`
- [ ] 1.5 Implementar o cenário do dólar (interpolação Focus, bandas e prêmio DOL de curto prazo) em `application/market/forecast.py` e verificar com testes de alvo, bandas e Focus ausente
- [ ] 1.6 Implementar o cenário estatístico do ouro (drift encolhido, EWMA, bandas 80/95) em `application/market/forecast.py` e verificar determinismo, bandas crescentes e histórico insuficiente
- [ ] 1.7 Implementar os indicadores de política (prêmio a termo, prêmio DOL, gap Focus, vol 30/90 e regime) em `application/market/indicators.py` e verificar cada sinal e a omissão por insumo ausente
- [ ] 1.8 Implementar os payloads de histórico, cenário e indicadores em `application/market/payloads.py` e verificar os formatos consumidos por CLI, MCP e gráfico
- [ ] 1.9 Implementar os formatadores CSV/JSON em `application/market/export.py` e verificar colunas, delimitador, datas ISO e bandas

## 2. Infraestrutura, cache e pré-cálculo

- [ ] 2.1 Criar o cliente BCB SGS 1 e o cliente Focus em `infrastructure/market/bcb_client.py`, com timeout, retry e parsing por fixture; verificar com testes que não acessam a rede
- [ ] 2.2 Criar o cliente B3 para `HistoricalExchange` e futuros DOL em `infrastructure/market/b3_client.py`, normalizando DOL de R$/US$ 1.000 para BRL/USD; verificar com fixtures e teste de unidade
- [ ] 2.3 Criar o cliente XAU/USD do Yahoo GC=F em `infrastructure/market/gold_client.py`, com User-Agent, timeout e parsing por fixture; verificar que falha de rede não derruba a aplicação
- [ ] 2.4 Implementar o cache bruto por fonte/data com TTL por recência, proveniência, busca incremental e escrita atômica em `infrastructure/market/raw_cache.py`; verificar com testes de TTL, imutabilidade, lacuna e leitura somente de cache
- [ ] 2.5 Implementar o cache derivado e o pré-cálculo por hash em `infrastructure/market/precompute_cache.py`, com manifesto, lock e escrita atômica; verificar reutilização, invalidação e falha preservando o artefato anterior
- [ ] 2.6 Implementar o housekeeping de 3 anos em `infrastructure/market/housekeeping.py`, relativo à maior data disponível; verificar remoção, retenção e arquivo corrompido
- [ ] 2.7 Montar a fábrica de serviços de mercado em `infrastructure/market/__init__.py` (ou módulo de composição equivalente) e verificar com um teste de integração usando adaptadores falsos, sem rede

## 3. Aba e gráficos

- [ ] 3.1 Criar o view-model headless da aba de mercado em `presentation/market_view_model.py` (estado, mensagens, opções, status e defasagem) e verificar com testes sem Tkinter
- [ ] 3.2 Criar os dados de gráfico headless (painéis empilhados, base 100, faixa mín-máx, bandas e overlay Fibonacci) em `presentation/market_chart_data.py` e verificar com testes de reindexação e níveis
- [ ] 3.3 Criar o renderizador matplotlib em `presentation/charts_market.py` consumindo apenas os dados de 3.2; verificar com teste de fumaça sem display quando possível
- [ ] 3.4 Criar a sub-aba GUI `presentation/gui/market_tab.py` (`Dólar e Ouro`) com controles, status, selo de defasagem, carregamento inicial só de cache e `Atualizar` próprio; verificar o controlador headless e fazer smoke manual da sub-aba
- [ ] 3.5 Registrar a aba `Câmbio e Ouro` como sub-notebook lazy entre `Tesouro Direto` e `Sobre` em `presentation/gui/shell.py`, com a sub-aba `Dólar e Ouro`; verificar com teste headless do registro e smoke manual da ordem das abas e sub-abas
- [ ] 3.6 Ligar o pré-cálculo ao `Atualizar` da sub-aba `Dólar e Ouro`, preservando o artefato anterior em falha; verificar com teste de integração com adaptadores falsos e smoke manual do status

## 4. CLI

- [ ] 4.1 Adicionar o subcomando `mercado` e suas opções ao `presentation/cli_parser.py`; verificar com testes de `--help`, padrões e rejeição de datas inválidas
- [ ] 4.2 Implementar o handler `mercado` em `presentation/cli_commands.py`, reutilizando os serviços de aplicação; verificar histórico, cenário, JSON, `--ativo` e códigos de retorno
- [ ] 4.3 Montar o handler no composition root `presentation/cli.py`; verificar que `mercado` sem `--atualizar` e sem `--no-cache` não acessa a rede
- [ ] 4.4 Implementar as regras de `--saida` (stdout, arquivo, diretório, nomes padrão e múltiplos artefatos); verificar cada caso com testes de escrita em diretório temporário
- [ ] 4.5 Documentar o subcomando em `docs/misc/cli.md` e no `README.md`; verificar executando os exemplos documentados em um diretório temporário

## 5. MCP

- [ ] 5.1 Adicionar `mercado_serie`, `mercado_previsao`, `mercado_indicadores` e `mercado_exportar` ao catálogo em `presentation/mcp/catalog.py`; verificar com teste do catálogo e das anotações somente leitura
- [ ] 5.2 Implementar o parsing de entrada e os handlers em `presentation/mcp/tool_inputs.py` e `presentation/mcp/tool_handlers.py`; verificar paginação, filtros, `sem_dados` e ausência de rede
- [ ] 5.3 Injetar o cache de mercado no contexto e no comando MCP; verificar que as tools leem apenas o cache e não gravam arquivos
- [ ] 5.4 Documentar as tools em `docs/misc/mcp.md` e no `README.md`; verificar a lista de tools e exemplos de chamada

## 6. Integração e validação

- [ ] 6.1 Executar um fluxo headless completo com fixtures gravadas (raw -> derivado -> pré-calculado -> payload) e verificar que a segunda execução reutiliza o artefato sem recalcular
- [ ] 6.2 Executar `make lint` e corrigir todas as falhas
- [ ] 6.3 Executar `make complexity` e corrigir todas as falhas
- [ ] 6.4 Executar `make test` (justificado por alterar shell, contratos de CLI e catálogo MCP) e corrigir todas as falhas
- [ ] 6.5 Fazer o smoke manual da sub-aba `Dólar e Ouro`: primeira exibição sem rede, `Atualizar`, alternância base 100, overlay Fibonacci, selo de defasagem e status; registrar o resultado

## Workflow follow-up

- Atualizar `CHANGELOG.md` com a skill de changelog após a implementação.
- Arquivar a change somente depois da revisão e do quality gate do projeto.
