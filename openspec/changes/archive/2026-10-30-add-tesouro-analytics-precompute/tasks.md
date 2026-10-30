# Tasks

## 1. Agregação em lote na aplicação

- [x] 1.1 Criar uma função pura em `application/tesouro/` que percorra vendas, resgates e estoque uma vez e devolva `SeriesPoint` por família, produto e bucket; verificar com teste que os pontos coincidem com o `TesouroSeriesProvider` atual para os mesmos dados.
- [x] 1.2 Cobrir os buckets mensal de estoque e diário/semanal/mensal de demanda e fluxo, incluindo janela vazia, título desconhecido e ausência de períodos futuros; verificar com testes headless.
- [x] 1.3 Garantir que a agregação seja independente de janela e use `Decimal` no cálculo; verificar teste que filtra a mesma série para 14d, 3m, 12m e 3a e compara com o provider atual.
- [x] 1.4 Exportar a função pela API pública de `application/tesouro/` e verificar teste de importação headless e `tests/test_architecture.py`.

## 2. Persistência e invalidação das séries

- [x] 2.1 Estender o cache analítico para snapshots fixos `series/estoque`, `series/demanda` e `series/fluxo`, com `schema_version`, hashes das fontes, metadados de status e `Decimal` serializado como string; verificar teste de escrita atômica, leitura e miss por esquema antigo.
- [x] 2.2 Implementar leitura estrita por hashes esperados, tratando arquivo ausente, corrompido ou hash divergente como miss sem remover nem renomear arquivos; verificar com testes de corrupção e somente leitura.
- [x] 2.3 Implementar o cálculo de `sha256` dos CSVs brutos usados por cada snapshot (`estoque`, `vendas`, `vendas+recompras`); verificar teste que muda o conteúdo e detecta hash novo, e que `checked_at`/`304` não alteram o hash.
- [x] 2.4 Implementar o coordenador de pré-cálculo que compara hashes, reutiliza o `AnaliseData` já parseado, adquire o lock analítico, reconfere os hashes e grava apenas as fontes alteradas; verificar testes de fonte alterada, conteúdo idêntico, falha isolada e chamadas concorrentes sem gravação duplicada.
- [x] 2.5 Garantir que os snapshots sejam limitados a 3 anos ancorados em `latest_data_date` e que o housekeeping por período não os remova; verificar teste com fonte atrasada e partições antigas.

## 3. Consumo na GUI

- [x] 3.1 Permitir que `AnaliseData` carregue um provider já pronto e fazer `TesouroAnaliseController` usá-lo sem reconstruir a partir dos registros; verificar testes headless do controller e do view-model.
- [x] 3.2 Alterar `presentation/tesouro_loaders.py` para montar o provider a partir dos snapshots via dependência injetada, com fallback único ao cache bruto quando os snapshots faltarem; verificar testes de hit, fallback com cache bruto e ausência total de cache.
- [x] 3.3 Injetar o adaptador de snapshots e o coordenador em `GuiDependencies` e montá-los em `presentation/gui/launch.py`; verificar teste de composição e `tests/test_architecture.py` sem novas exceções de camada.
- [x] 3.4 Disparar o pré-cálculo após o refresh bem-sucedido em `TesouroSubTab._load_worker`, fora da thread da UI, apenas quando o hash da fonte mudar; verificar teste headless de gatilho, ausência de gatilho em `304` e isolamento de falha.
- [x] 3.5 Garantir que a troca de janela use as séries pré-calculadas sem chamar o loader bruto; verificar teste headless que alterna 14d/3m/12m/3a e confirma ausência de parse/rede.
- [x] 3.6 Manter `tests/test_ui_test_budget.py` no orçamento atual; verificar que nenhum teste novo importa Tkinter sem marcação e que o total não aumenta.

## 4. Documentação e validação

- [x] 4.1 Atualizar `docs/misc/datasources.md` com o layout `analytics/series/`, os hashes por fonte, a invalidação e o fallback; verificar que os caminhos e comportamentos descritos correspondem ao código.
- [x] 4.2 Rodar `make lint` e `make complexity` e corrigir violações; verificar saída sem erros.
- [x] 4.3 Rodar os testes diretamente relacionados (`test_tesouro_analytics_cache.py`, `test_tesouro_series.py`, `test_tesouro_loaders.py`, `test_tesouro_analise_controller.py`, `test_tesouro_analise_gui_view_model.py` e novos testes) e verificar que passam.
- [x] 4.4 Rodar `make test` (justificado por cache, séries e contratos compartilhados) e registrar o resultado.

## Workflow follow-up

- Revisar a change com o usuário e arquivar após a aprovação.
- Teste manual opcional: abrir a GUI com cache bruto existente e sem `analytics/series`; confirmar que a primeira exibição monta as séries uma vez e fica rápida nas próximas; clicar em `Atualizar` e confirmar que um `304` não recalcula; alternar 14d/3m/12m/3a e confirmar que não há novo parse.
