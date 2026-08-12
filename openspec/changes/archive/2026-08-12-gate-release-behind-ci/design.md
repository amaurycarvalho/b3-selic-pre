## Context

Atualmente, o `release.yml` constrói binários PyInstaller em 3 plataformas e publica a GitHub Release sem verificar qualidade do código. O `ci.yml` tem um job monolítico `lint_and_test` que roda apenas em push/PR para `main`, sem suporte a `workflow_call`. A RFC-002 (seções 3.3 e 4.1) define a arquitetura desejada: `ci.yml` reutilizável com jobs em cadeia, e `release.yml` gateado por ele.

## Goals / Non-Goals

**Goals:**
- `ci.yml` expõe `workflow_call` para ser chamado como gate do release
- `ci.yml` é refatorado em 3 jobs encadeados: `lint` → `test` → `quality-gate`
- `release.yml` adiciona job `ci` que chama `ci.yml`; `build` passa a `needs: ci`
- O Makefile ganha todos os targets do quality gate definidos na RFC-002
- Releases que falham o quality gate não produzem binários

**Non-Goals:**
- Alterar thresholds ou ferramentas do quality gate (já definidos na RFC-002)
- Executar `mutmut run` no CI (mutation-check apenas lê stats pré-gerados; `mutation-run` é manual)
- Migrar outras dependências além das listadas na RFC-002
- Modificar o formato da GitHub Release (body via CHANGELOG.md mantido)

## Decisions

### 1. `workflow_call` como mecanismo de reuso

**Decisão:** `ci.yml` expõe trigger `workflow_call` e `release.yml` o chama.

**Alternativa considerada:** Duplicar os steps do CI dentro do `release.yml`. Rejeitada — fragiliza manutenção e viola DRY.

**Alternativa considerada:** Composite action. Rejeitada — composite actions não suportam condicionais complexas nem cache entre jobs como `workflow_call` + reuso de workflow permite.

### 2. Jobs encadeados (`lint` → `test` → `quality-gate`)

**Decisão:** Pipeline sequencial onde cada job só roda se o anterior passar. `lint` falha rápido (rápido, pega erros triviais). `test` roda em matrix Python 3.12 + 3.13. `quality-gate` roda complexidade + duplicação + segurança + mutation-check como bloco final.

**Alternativa considerada:** Job único monolítico. Rejeitada — dificulta identificar falha rápida, impossibilita paralelismo parcial e complica o cache.

### 3. Python 3.12 como baseline, 3.12+3.13 como matrix

**Decisão:** `lint` roda em 3.12. `test` e `quality-gate` rodam em matrix 3.12 + 3.13, já que a RFC-002 define compatibilidade com ambas as versões.

**Alternativa considerada:** Manter Python 3.10. Rejeitada — a RFC-002 migra para 3.12+3.13 como parte da modernização do pipeline.

### 4. Cache de `.venv` no job `quality-gate`

**Decisão:** O job `quality-gate` faz cache de `.venv` com key baseada em SO + versão Python + hash de `pyproject.toml`. Isso evita reinstalar dependências pesadas (semgrep, radon, mutmut) a cada execução.

### 5. Mutation check sem execução de `mutmut run`

**Decisão:** O job `quality-gate` executa apenas `make mutation-check` (que lê `mutants/mutmut-cicd-stats.json` pré-existente). `make mutation-run` é manual e não roda no CI.

**Motivação:** `mutmut run` é extremamente lento (horas) e inviável no CI. O workflow espera que o desenvolvedor gere os stats localmente antes do push.

## Risks / Trade-offs

- **Release bloqueada por falha no quality gate** → Mitigação: o desenvolvedor pode rodar `make quality-gate` localmente antes de criar a tag, tendo feedback imediato. Releases manuais (`workflow_dispatch`) permitem re-tentativa após correção.
- **Tempo de CI aumentado no release** → Mitigação: cache de `.venv` reduz reinstalação. O job `ci` inteiro roda antes do build — é o preço da garantia de qualidade.
- **`mutation-check` depende de stats pré-gerados** → Risco de release passar sem mutation testing recente. Mitigação: documentar no workflow que o dev deve rodar `make mutation-run` antes do push da tag. A RFC-002 já prevê isso.
- **Makefile completamente substituído** → Risco de regressão em targets existentes (`install`, `build`, `test`, `lint`). Mitigação: os novos targets mantêm compatibilidade com os antigos e apenas adicionam novos.

## Open Questions

- Nenhuma — a RFC-002 já cobre todas as decisões de design necessárias. A implementação segue estritamente o que foi especificado lá.
