## Context

O `mutmut run` (commit `6c28ac1`, mutmut 3.7.0) deixou os resultados em `mutants/`:

- `mutants/mutmut-cicd-stats.json` — agregados: `killed=2057`, `survived=1192`, `no_tests=85`, `timeout=4`, `total=3338`.
- `mutants/src/**/*.py.meta` — por arquivo, `exit_code_by_key` mapeia cada mutante a um exit code (0 = survived).
- `mutants/src/**/*.py` — código-fonte mutado com trampolines, contendo `x_<func>__mutmut_orig` (original) e `x_<func>__mutmut_N` (mutação N).
- `mutants/mutmut-stats.json` — hashes de funções, dependências e mapeamento função→testes.

Restrições:
- Nunca rodar `mutmut` (nem `run`, nem `results`). A identificação dos survivors é 100% derivada dos artefatos acima.
- O `src/` atual está no mesmo commit do run, então as funções originais batem com `x_<func>__mutmut_orig`.

## Goals / Non-Goals

**Goals:**
- Matar, com testes, o máximo de survivors matáveis, agrupados por módulo, em ordem de custo × impacto.
- Documentar os mutantes equivalentes (impossíveis de matar) e pulá-los.
- Manter `make lint` e `make test` (coverage >= 85%) verdes.

**Non-Goals:**
- Alterar comportamento de código de produção.
- Executar `mutmut` para validar — validação é via `pytest` do teste específico.
- Perseguir mutantes `no_tests` (85) ou `timeout` (4) — escopo é só `survived`.
- Perseguir o score de 80% em si; o objetivo é matar survivors, não recalibrar o gate.

## Decisions

### D1 — Identificação dos survivors sem rodar mutmut

Ler os `.meta` e considerar survivor todo mutante com `exit_code == 0`. Fonte de verdade: `mutants/src/**/*.meta`, cruzado com `mutants/mutmut-cicd-stats.json` (confirma 1192).

- Alternativa rejeitada: `mutmut results` / `mutmut show` — exige `.mutmut-cache` (ausente) e viola a restrição de não rodar mutmut.

### D2 — Mapeamento survivor → mutação concreta

Para cada chave `x_<func>__mutmut_N` sobrevivente, o diff é obtido comparando `x_<func>__mutmut_orig` com `x_<func>__mutmut_N` no `mutants/src/**/<mod>.py`. Isso revela a linha e o operador exatos da mutação, permitindo escrever o teste no `src/` atual (mesmo commit).

- Alternativa rejeitada: reconstruir via libcst/mutmut em tempo de implementação — desnecessário, o diff já está materializado nos `.py`.

### D3 — Classificação em três categorias

1. **Matável** — existe input/assertiva que distingue a mutação → escrever teste.
2. **Equivalente** — comportamento idêntico para todo input (ex.: `.replace(".", ",")` → `.replace("XX.XX", ",")` quando o valor nunca contém `XX.XX`) → pular e documentar numa lista de exceção.
3. **Já coberto** — comportamento mutado já é coberto por assertiva existente (falso survivor) → pular, sem teste novo.

### D4 — Lista de exceção documentada

Os equivalentes serão registrados num artefato de acompanhamento (seção no `tasks.md` ou arquivo `docs/`/nota no change) com `chave_do_mutante → motivo da equivalência`, para rastreabilidade futura.

- Alternativa rejeitada: marcar com `# pragma: no mutate` no código — alteraria código de produção, fora do escopo (deixado como opção futura).

### D5 — Ordem de ataque por módulo (custo × impacto)

1. `application.use_cases` (2) e `application.formatting` (1) — quase zerados, fecham rápido.
2. `infrastructure.disk_cache` (42) — TTL/parse, testes já em `test_disk_cache.py`.
3. `infrastructure.cached_client` (111) — alta taxa de sobrevivência (~75%).
4. `infrastructure.b3_client` (80) — normalização/paginação/encoding.
5. `application.analyze.*` (_texto 60, _evolucao 63, _resumo 96, _texto_evolucao 99) — lógica textual, cada survivor tende a ser condição de borda.
6. `presentation.cli` (46) e `presentation.settings` (56) — parsing de args e XDG.
7. `presentation.charts` (421) — maior volume; muitos são mutações visuais, avaliar custo/benefício por função.
8. `infrastructure.desktop` (89) — XDG/env, exige mocks de `os.environ`.

### D6 — Posicionamento dos testes

Estender os arquivos existentes por afinidade de módulo (`test_b3_selic_pre.py`, `test_disk_cache.py`, `test_evolucao_resumo.py`, `test_novo_resumo.py`); criar arquivo novo apenas se nenhum corresponder.

### D7 — Validação

Rodar somente o teste modificado/inserido (`pytest tests/<arquivo>::<classe>::<teste>`). Ao final, `make lint` e `make test`. Nunca `mutmut`.

## Risks / Trade-offs

- **Classificação de equivalente é heurística** → documentar o raciocínio de cada caso; na dúvida, tratar como matável e escrever o teste.
- **`charts` com 421 survivors** → muitas mutações visuais podem exigir asserts frágeis; priorizar funções com lógica determinística e documentar as visuais como não cobertas se o custo for alto.
- **`desktop`/`settings` dependem de XDG/env** → usar monkeypatch de `os.environ`; portabilidade entre plataformas deve ser considerada.
- **Risco de teste novo ser redundante/inflar a suíte** → antes de escrever, verificar a cobertura existente via `mutants/mutmut-stats.json` (`tests_by_mangled_function_name`).
- **Cobertura pode cair se só adicionar asserts** → adicionar testes que também aumentem cobertura de linhas, não apenas de mutantes.

## Open Questions

- Confirmar se a lista de equivalentes deve ir em `docs/` ou apenas no change (tasks/design).
- Definir um corte para `charts`: perseguir todos os 421 ou apenas os de lógica não-visual?
