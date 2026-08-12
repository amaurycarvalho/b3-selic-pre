## ADDED Requirements

### Requirement: CI workflow reutilizável via workflow_call
O workflow `ci.yml` SHALL expor o trigger `workflow_call` para ser invocado como gate de qualidade por outros workflows, em adição aos triggers existentes `push` e `pull_request`.

#### Scenario: workflow_call exposto
- **WHEN** outro workflow define um job que referencia `uses: ./.github/workflows/ci.yml`
- **THEN** o `ci.yml` é executado com todos os seus jobs na ordem definida
- **THEN** o resultado (sucesso ou falha) é propagado ao workflow chamador

### Requirement: Pipeline CI com jobs encadeados
O workflow `ci.yml` SHALL executar os jobs em sequência `lint` → `test` → `quality-gate`, onde cada job depende do sucesso do anterior.

#### Scenario: lint executa primeiro
- **WHEN** o workflow é disparado
- **THEN** o job `lint` executa `make install` e `make lint` em Python 3.12
- **THEN** falha em `lint` impede a execução dos jobs subsequentes

#### Scenario: test executa após lint
- **WHEN** o job `lint` conclui com sucesso
- **THEN** o job `test` executa `make install` e `make test` em matrix Python 3.12 e 3.13
- **THEN** falha em qualquer versão do `test` impede a execução de `quality-gate`

#### Scenario: quality-gate executa após test
- **WHEN** o job `test` conclui com sucesso em todas as versões
- **THEN** o job `quality-gate` executa `make install-quality-tools` e `make quality-gate` em matrix Python 3.12 e 3.13
- **THEN** o job faz cache de `.venv` com key composta por SO + versão Python + hash de `pyproject.toml`
- **THEN** os artefatos `coverage.xml` e `mutation_report.html` são enviados como artifacts do workflow

### Requirement: Quality gate abrange todas as verificações
O target `make quality-gate` SHALL executar sequencialmente: lint, complexidade (radon + xenon + lizard + complexity_metrics.py), duplicação (jscpd), testes com cobertura (pytest-cov >= 85%), segurança (semgrep ERROR blocking, WARNING reportado) e mutation check (score >= 80%).

#### Scenario: quality-gate passa
- **WHEN** todas as verificações individuais passam
- **THEN** `make quality-gate` retorna exit code 0

#### Scenario: quality-gate falha
- **WHEN** qualquer verificação bloqueante falha (lint, complexidade < 30 MI, duplicação > 10%, cobertura < 85%, semgrep ERROR > 0, mutation score < 80%)
- **THEN** `make quality-gate` retorna exit code != 0

### Requirement: Mutation check sem execução de mutmut
O job `quality-gate` SHALL executar apenas `make mutation-check` (que lê `mutants/mutmut-cicd-stats.json` pré-existente), nunca `make mutation-run` (que executaria `mutmut run` e geraria os stats).

#### Scenario: mutation-check no CI
- **WHEN** o job `quality-gate` executa `make quality-gate`
- **THEN** o target `mutation-check` lê `mutants/mutmut-cicd-stats.json`
- **THEN** se o arquivo não existe ou o score é < 80%, o gate falha

#### Scenario: mutation-run é manual
- **WHEN** um desenvolvedor deseja gerar stats de mutação
- **THEN** ele executa `make mutation-run` localmente (nunca no CI)
- **THEN** o resultado é commitado como `mutants/mutmut-cicd-stats.json`
