## 1. Guard de fronteiras de camada

- [x] 1.1 Criar `tests/architecture_allowlist.py` com aprovações explícitas e justificativas para as dívidas conhecidas
- [x] 1.2 Criar `tests/test_architecture.py` com verificação AST das dependências entre `domain`, `application`, `infrastructure` e `presentation`
- [x] 1.3 Adicionar verificação de pureza de `domain` e de ausência de UI/rede em `application`
- [x] 1.4 Adicionar verificação de aprovações obsoletas para forçar limpeza após refatorações

## 2. Orçamento de testes de UI

- [x] 2.1 Registrar o marker `ui` em `pyproject.toml`
- [x] 2.2 Marcar as classes de teste de GUI existentes com `@pytest.mark.ui`
- [x] 2.3 Criar `tests/test_ui_test_budget.py` com contagem estática, hard cap e exigência de marcação
- [x] 2.4 Definir o baseline atual de 22 testes de UI e documentar que o orçamento só pode diminuir

## 3. Protocolo de validação de changes

- [x] 3.1 Documentar em `AGENTS.md` (ou documento equivalente) que toda change deve finalizar com `make lint`, `make complexity` e os testes diretamente impactados
- [x] 3.2 Documentar quando a suíte completa é obrigatória e quando o último passo deve ser um teste manual opcional do usuário
- [x] 3.3 Validar esta change executando `make lint`, `make complexity` e os testes de guarda (`pytest tests/test_architecture.py tests/test_ui_test_budget.py`)
