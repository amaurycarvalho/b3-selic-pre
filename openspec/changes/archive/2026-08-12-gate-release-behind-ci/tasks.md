## 1. Makefile

- [x] 1.1 Substituir Makefile atual pela versão completa da RFC-002 com todos os targets de qualidade (quality-gate, complexity, duplication, mutation-check, mutation-run, mutation-stats, mutation-results, security, security-all, security-changed, install-quality-tools)
- [x] 1.2 Verificar que os targets existentes (install, build, test, lint, clean) permanecem funcionais após a substituição

## 2. CI Workflow

- [x] 2.1 Adicionar trigger `workflow_call:` ao `ci.yml` para permitir reuso pelo release
- [x] 2.2 Refatorar job `lint_and_test` em job `lint` dedicado (Python 3.12, `setup-python@v5`)
- [x] 2.3 Adicionar job `test` com `needs: lint`, matrix Python 3.12 + 3.13, `setup-python@v5`
- [x] 2.4 Adicionar job `quality-gate` com `needs: test`, matrix Python 3.12 + 3.13, `setup-python@v5`
- [x] 2.5 Adicionar cache de `.venv` no job `quality-gate` (key: OS + Python version + hash pyproject.toml)
- [x] 2.6 Adicionar step `make install-quality-tools` antes de `make quality-gate`
- [x] 2.7 Adicionar upload de artifacts `coverage.xml` e `mutation_report.html` no job `quality-gate`

## 3. Release Workflow

- [x] 3.1 Adicionar job `ci` que chama `ci.yml` via `uses: ./.github/workflows/ci.yml` (workflow_call)
- [x] 3.2 Adicionar `needs: ci` ao job `build`
- [x] 3.3 Garantir que job `release` já possui `needs: build` (gate transitivo)

## 4. ADR

- [x] 4.1 Criar `docs/adrs/ADR-002.md` documentando a decisão de gatear releases atrás do quality gate do CI

## 5. Verificação

- [x] 5.1 Executar `make quality-gate` localmente e confirmar que todos os checks passam
- [x] 5.2 Validar sintaxe YAML dos workflows (`ci.yml` e `release.yml`)
