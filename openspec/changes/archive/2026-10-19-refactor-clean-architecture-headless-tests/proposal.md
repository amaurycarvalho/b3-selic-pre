## Why

Os guardrails de arquitetura vão bloquear novas violações, mas as dívidas atuais continuam impedindo testes verdadeiramente headless e a reutilização de regras pela futura CLI. A camada de aplicação depende de `presentation.settings`, a `domain` conhece caminhos do sistema operacional, regras de negócio (data útil, janela de histórico, seleção de exportação, estatísticas) vivem nos mixins da GUI, e transformações puras de dados de gráfico estão em `presentation/charts.py`. Isso força testes de UI caros para validar comportamento que poderia ser testado sem Tk ou matplotlib.

## What Changes

- Remover a dependência `application -> presentation`: configurações passam a ser construídas a partir de mappings/dados simples; `Settings` continua na presentation/infrastructure de composição.
- Remover `os` da camada `domain`, movendo o caminho do atalho para `infrastructure/desktop.py`.
- Mover regras de negócio hoje embutidas na GUI para a camada de aplicação: data útil mais próxima, validação de data de consulta (futura/antiga), janela de histórico e estatísticas de taxas.
- Extrair a seleção de payload de exportação (bruto, consolidado, evolução) e o estado de habilitação de controles para um view-model/controlador headless, sem importar Tkinter.
- Mover transformações puras de dados de gráfico (`_nearest_ticks`, interpolações, grades 3D) de `presentation/charts.py` para a camada de aplicação.
- Expor `montar_evolucao_resumo` pela API pública de `application.analyze`, eliminando imports de módulos privados pela GUI.
- Reorganizar a CLI como composition root que instancia adapters e chama casos de uso, preparando a implementação futura de comandos por parâmetro sem duplicar regras da GUI.
- Migrar para testes headless os testes de UI que validam regras, exportação, dispatch de gráficos e estado de controles, mantendo em UI apenas testes de montagem/apresentação de widgets.
- Reduzir o UI test budget após a migração e remover as aprovações de arquitetura que deixarem de ser necessárias.

## Capabilities

### New Capabilities
- `headless-application-services`: serviços e transformações de aplicação sem dependência de Tkinter/matplotlib, configuração construída a partir de dados simples, view-model headless e composition root da CLI reutilizando casos de uso.

### Modified Capabilities
- `test-suite-performance`: migração de testes de UI para headless e redução do orçamento de testes dependentes de display.

## Impact

- `src/b3_selic_pre/application/analyze/_config.py`, `application/use_cases.py`, `application/formatting.py` e novos módulos de serviços/view-model.
- `src/b3_selic_pre/domain/constants.py` e `src/b3_selic_pre/infrastructure/desktop.py`.
- `src/b3_selic_pre/presentation/charts.py`, `presentation/cli.py` e mixins em `presentation/gui/`.
- `tests/test_b3_selic_pre_gui.py`, `tests/test_charts_data.py`, `tests/test_b3_selic_pre.py`, `tests/test_cli.py` e novos testes headless.
- `tests/architecture_allowlist.py` perde entradas conforme as dívidas são eliminadas; `UI_TEST_BUDGET` é reduzido.
- Sem mudança de comportamento observável para o usuário; comandos CLI novos ficam fora do escopo e serão tratados em change futura.
