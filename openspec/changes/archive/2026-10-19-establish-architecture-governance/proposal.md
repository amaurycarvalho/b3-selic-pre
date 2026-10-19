## Why

A aplicação já declara quatro camadas Clean Architecture, mas não há verificação automática das dependências entre elas. Hoje existem violações reais (por exemplo, `application/analyze/_config.py` importa `presentation/settings.py`) e nada impede que novas violações sejam introduzidas silenciosamente. Ao mesmo tempo, a suíte de testes de GUI pode crescer sem limite, tornando a validação mais lenta e dependente de display, o que dificulta testes headless e a futura implementação de comandos CLI que reutilizem partes da aplicação.

## What Changes

- Criar a capability de governança de arquitetura com regras explícitas de dependência entre `domain`, `application`, `infrastructure` e `presentation`.
- Adicionar testes de guarda que falham quando uma camada interna importa uma camada externa não aprovada.
- Introduzir um arquivo de aprovações explícitas (`tests/architecture_allowlist.py`) para dívidas conhecidas; novas exceções exigem alteração explícita nesse arquivo e revisão.
- Adicionar teste de guarda para pureza da camada `domain` e para ausência de dependências de UI/rede na camada `application`, viabilizando testes headless.
- Adicionar orçamento de testes de UI (UI test budget): todo teste que instancia Tk ou a aplicação GUI deve ser marcado com `@pytest.mark.ui`, a contagem não pode crescer e o orçamento só pode diminuir.
- Registrar `make lint`, `make complexity` e testes direcionados como validação obrigatória de toda change, reservando a suíte completa para mudanças com risco real de regressão.
- Definir no processo de change que, quando a suíte completa não for justificada, o último passo deve ser um teste manual opcional do usuário.

## Capabilities

### New Capabilities
- `architecture-governance`: regras de dependência entre camadas, aprovações explícitas, pureza das camadas internas, composição de casos de uso e protocolo de validação de changes.

### Modified Capabilities
- `test-suite-performance`: adiciona o orçamento de testes de UI e a exigência de marcar testes não headless, limitando o crescimento da suíte dependente de display.

## Impact

- Novos testes em `tests/test_architecture.py`, `tests/test_ui_test_budget.py` e `tests/architecture_allowlist.py`.
- `pyproject.toml` passa a registrar o marker `ui`.
- `tests/test_b3_selic_pre_gui.py` passa a marcar as classes de teste com `@pytest.mark.ui`.
- Nenhuma mudança de comportamento de produto; a refatoração das dívidas aprovadas fica para a change `refactor-clean-architecture-headless-tests`.
- O guard de arquitetura passa a bloquear novas violações de camada em `src/`.
