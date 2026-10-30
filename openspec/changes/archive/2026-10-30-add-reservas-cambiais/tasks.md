# Tasks

## 0. Pré-requisito de sequência

- [x] 0.1 Confirmar que `add-cambio-ouro-forecast` está implementado e arquivado, com `openspec/specs/market-data-cache/spec.md` existente; rodar os testes do core de mercado e verificar que `BcbSgsClient`, raw cache, precompute e housekeeping estão disponíveis

## 1. Domínio e serviços de aplicação

- [x] 1.1 Criar os modelos puros de reservas (`ReservesIndicators`, `ReservesRegime`, `ReservesThresholds`) em `domain/reserves.py` e verificar com testes de igualdade, unidades e valores ausentes
- [x] 1.2 Criar a configuração de reservas (janela padrão, sobreposição de revisão, TTLs, retenção e limiares de regime) em `application/reserves/config.py` e verificar com testes de defaults e sobrescrita por mapping
- [x] 1.3 Implementar parsing e normalização dos pontos do BCB (data `dd/mm/aaaa` para ISO, valor string para float em US$ milhões) em `application/reserves/series.py` e verificar com fixtures do SGS 13621
- [x] 1.4 Implementar a mescla incremental do snapshot com sobreposição de revisões e o hash canônico dos pares `(data, valor)` em `application/reserves/series.py` e verificar com testes de revisão, lacuna, janela retida e hash estável
- [x] 1.5 Implementar os indicadores (nível, variações de 1/3/12 meses, tendência de 90 dias, drawdown de 12 meses e posição na faixa) em `application/reserves/indicators.py` e verificar cada métrica com dados sintéticos e histórico insuficiente
- [x] 1.6 Implementar o regime determinístico `aumento | estavel | deterioracao` e a exposição dos limiares em `application/reserves/indicators.py` e verificar os três regimes, a borda dos limiares e o determinismo
- [x] 1.7 Implementar os payloads de série, indicadores e exportação em `application/reserves/payloads.py` e verificar os formatos consumidos por GUI, CLI e MCP
- [x] 1.8 Implementar os formatadores CSV/JSON em `application/reserves/export.py`, reutilizando os helpers de mercado, e verificar colunas, delimitador, datas ISO, unidade e nomes padrão

## 2. Infraestrutura, cache e pré-cálculo

- [x] 2.1 Estender o cache bruto de mercado para aceitar snapshot normalizado por fonte, com hash canônico, TTL por recência e escrita atômica, e verificar leitura somente de cache, expiração e snapshot sem regravação desnecessária
- [x] 2.2 Integrar o snapshot de reservas ao cache derivado e ao pré-cálculo por hash, com lock e manifesto, e verificar reutilização quando o hash não muda e invalidação quando um valor ou parâmetro muda
- [x] 2.3 Reutilizar o housekeeping de 3 anos ancorado na maior data para o namespace de reservas e verificar remoção, retenção, arquivo corrompido e não invalidação do pré-cálculo pela limpeza fora da janela
- [x] 2.4 Parametrizar o `BcbSgsClient` para o código 13621 e criar o adaptador de reservas com timeout, retry e parsing por fixture, verificando que os testes não acessam a rede
- [x] 2.5 Montar a fábrica de serviços de reservas no composition root de infraestrutura e verificar com um teste de integração usando adaptadores falsos, sem rede
- [x] 2.6 Implementar a leitura do artefato pré-calculado para GUI/CLI/MCP e verificar que a segunda leitura não recalcula e que a ausência do artefato devolve estado vazio sem rede

## 3. Aba e gráficos

- [x] 3.1 Criar o view-model headless da sub-aba em `presentation/reserves_view_model.py` (estado, janela, indicadores, regime, defasagem e mensagens) e verificar com testes sem Tkinter
- [x] 3.2 Criar os dados de gráfico headless (janela 12m/3a, médias móveis, faixa, máximo/mínimo e selo de regime) em `presentation/reserves_chart_data.py` e verificar com testes de recorte e indicadores
- [x] 3.3 Criar o renderizador matplotlib em `presentation/charts_reserves.py` consumindo apenas os dados de 3.2 e verificar com teste de fumaça sem display
- [x] 3.4 Criar a sub-aba GUI `presentation/gui/reserves_sub_tab.py` com controles, status, selo de defasagem, carregamento inicial só de cache e `Atualizar` próprio; verificar o controlador headless e fazer smoke manual da sub-aba
- [x] 3.5 Registrar a sub-aba `Reservas Internacionais` no sub-notebook de `Câmbio e Ouro`, após `Dólar e Ouro`, e verificar com teste headless de ordem, lazy e segunda exibição
- [x] 3.6 Ligar o pré-cálculo ao `Atualizar` da sub-aba, preservando o artefato anterior em falha, e verificar com teste de integração com adaptadores falsos e smoke manual do status

## 4. CLI

- [x] 4.1 Adicionar o subcomando `reservas` e suas opções ao `presentation/cli_parser.py` e verificar com testes de `--help`, janela padrão, `--janela 3a` e rejeição de datas inválidas
- [x] 4.2 Implementar o handler `reservas` em `presentation/cli_commands.py`, reutilizando os serviços de aplicação, e verificar CSV, JSON, `--indicadores` no payload, `--saida` e códigos de retorno
- [x] 4.3 Montar o handler no composition root `presentation/cli.py` e verificar que `reservas` sem `--atualizar` e sem `--no-cache` não acessa a rede
- [x] 4.4 Implementar as regras de `--saida` para `reservas-serie.csv` e `reservas.json`, incluindo diretório, arquivo e falha de escrita, com testes em diretório temporário
- [x] 4.5 Documentar o subcomando em `docs/misc/cli.md` e no `README.md` e verificar executando os exemplos documentados em um diretório temporário

## 5. MCP

- [x] 5.1 Adicionar `reservas_serie`, `reservas_indicadores` e `reservas_exportar` ao catálogo em `presentation/mcp/catalog.py` e verificar o catálogo e as anotações somente leitura
- [x] 5.2 Implementar o parsing de entrada e os handlers em `presentation/mcp/tool_inputs.py` e `presentation/mcp/tool_handlers.py` e verificar filtros de janela, paginação, `sem_dados` e ausência de rede
- [x] 5.3 Injetar o cache/artefato de reservas no contexto e no comando MCP e verificar que as tools leem apenas o cache e não gravam arquivos
- [x] 5.4 Documentar as tools em `docs/misc/mcp.md` e no `README.md` e verificar a lista de tools e exemplos de chamada

## 6. Integração e validação

- [x] 6.1 Executar um fluxo headless completo com fixtures gravadas (snapshot bruto -> pré-calculado -> payload -> CLI/MCP) e verificar que a segunda execução reutiliza o artefato sem recalcular
- [x] 6.2 Executar `make lint` e corrigir todas as falhas
- [x] 6.3 Executar `make complexity` e corrigir todas as falhas
- [x] 6.4 Executar `make test` (justificado por alterar sub-notebook, CLI e catálogo MCP) e corrigir todas as falhas
- [x] 6.5 Fazer o smoke manual da sub-aba: primeira exibição sem rede, `Atualizar`, janelas 12m/3a, selo de regime, aviso de defasagem e status; registrar o resultado

## Workflow follow-up

- Arquivar `add-cambio-ouro-forecast` antes desta change, porque o delta de `market-data-cache` depende da spec criada por ela.
- Atualizar `CHANGELOG.md` com a skill de changelog após a implementação.
- Arquivar esta change somente depois da revisão e do quality gate do projeto.
- Verificar o resultado arquivado.
