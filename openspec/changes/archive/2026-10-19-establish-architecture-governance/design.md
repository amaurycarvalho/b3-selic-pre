## Context

O pacote já usa o layout `domain/`, `application/`, `infrastructure/` e `presentation/`, mas as fronteiras são apenas convenção. O import real mostra uma dependência de `application` para `presentation` (`application/analyze/_config.py`), `domain` importando `os` (`domain/constants.py`) e a GUI instanciando diretamente adapters de infraestrutura. Também não existe limite para o crescimento dos testes de GUI, que são caros e dependem de display.

Ver `proposal.md` para a motivação. Este design registra como os guardrails são implementados e como as exceções atuais serão tratadas.

## Goals / Non-Goals

**Goals:**
- Detectar violações de camada estaticamente, sem importar os módulos e sem exigir Tk/matplotlib/rede.
- Ter um mecanismo explícito e auditável para dívidas arquiteturais conhecidas.
- Impedir crescimento dos testes de UI não headless.
- Tornar o protocolo de validação de changes verificável e repetível.

**Non-Goals:**
- Corrigir as dívidas atuais de camada nesta change; isso pertence a `refactor-clean-architecture-headless-tests`.
- Implementar novos comandos CLI.
- Alterar o comportamento visível do produto.
- Substituir lint, complexidade, cobertura ou mutation testing existentes.

## Decisions

### 1. Análise estática via AST em vez de importação dos módulos

**Decisão:** O teste de arquitetura percorre `src/b3_selic_pre/**/*.py`, extrai imports com `ast` e calcula a camada do módulo importador e do importado.

**Alternativas consideradas:**
- Importar cada módulo e inspecionar `sys.modules`: falha em ambiente headless por causa de Tk/matplotlib e pode executar efeitos colaterais.
- Ferramenta externa de arquitetura: adiciona dependência e configuração novas para uma regra simples.

**Racional:** AST é determinístico, rápido, não exige display e cobre imports dentro de funções, que são usados no projeto.

### 2. Aprovações explícitas em arquivo versionado

**Decisão:** Manter `tests/architecture_allowlist.py` com pares `(módulo importador, camada/import externo)` e justificativa. O teste falha para violações não aprovadas e também para aprovações obsoletas.

**Alternativa considerada:** Lista de exceções embutida no teste. Foi rejeitada por dificultar revisão e justificativa por entrada.

**Racional:** Adicionar uma exceção passa a ser uma alteração explícita e revisável; remover uma dívida força a limpeza da aprovação correspondente.

### 3. Regras de pureza separadas por camada

**Decisão:** Além do grafo entre camadas, o guard verifica imports externos proibidos: `domain` sem I/O/UI/rede/frameworks, `application` sem UI/rede e `infrastructure` sem UI.

**Alternativa considerada:** Apenas o grafo entre pacotes internos. Foi rejeitada porque `domain/constants.py` importar `os` não apareceria como violação de camada, mas continua impedindo pureza e testes triviais.

### 4. Orçamento de UI por contagem estática de testes marcados

**Decisão:** Contar testes com `@pytest.mark.ui` via AST em `tests/test_*.py`. O orçamento atual é 22 (baseline) e existe um hard cap de 22. Ao migrar um teste para headless, o orçamento deve ser reduzido.

**Alternativas consideradas:**
- Coletar com `pytest --collect-only -m ui`: mais fiel, porém acopla o guard ao processo de coleta e pode ser afetado por plugins/configuração.
- Marcar apenas arquivos: menos granular e não impede adicionar testes UI em arquivos existentes.

**Racional:** A contagem estática é simples, rápida e suficiente para impedir regressão. A marcação `ui` também permite rodar `pytest -m ui` quando necessário.

### 5. Protocolo de validação documentado na spec, não automatizado no guard

**Decisão:** O protocolo (`make lint`, `make complexity`, testes direcionados, suíte completa só com justificativa e teste manual opcional) fica na spec de governança e nas tarefas das changes. Não é criado um script que tenta inferir risco de regressão.

**Alternativa considerada:** Automatizar a decisão de rodar a suíte completa. Rejeitada porque a avaliação de risco depende do escopo da change e seria frágil.

## Risks / Trade-offs

- **[Falso positivo em import legítimo de composition root]** → Composition roots e `__main__` são tratados fora das camadas; `presentation.cli -> infrastructure` permanece aprovado explicitamente.
- **[Aprovação ampla demais]** → A chave é `(módulo importador, camada importada)`, então uma nova importação no mesmo arquivo não exige nova entrada. Risco aceito nesta fase; a refatoração elimina as entradas da GUI.
- **[Orçamento de UI desatualizado após migração]** → O teste de aprovação obsoleta não se aplica ao orçamento; a tarefa de migração exige reduzir `UI_TEST_BUDGET` junto com a mudança.
- **[Teste de arquitetura não cobre imports dinâmicos]** → `importlib` e imports por string não são detectados. O projeto não usa esse padrão hoje; revisão de código continua necessária.

## Migration Plan

1. Adicionar os testes de guarda e o marker `ui` sem alterar comportamento.
2. Marcar os testes de GUI existentes como `ui`; o baseline de 22 é aceito como dívida.
3. Aplicar a change de refatoração para corrigir as dívidas e reduzir o orçamento.
4. Remover entradas de `tests/architecture_allowlist.py` conforme cada dívida for corrigida.
