## 1. Levantamento dos survivors

- [x] 1.1 Ler `mutants/src/**/*.meta` e extrair todos os mutantes com `exit_code == 0` (survivors), agrupando por módulo e função
- [x] 1.2 Conferir o total (1192) contra `mutants/mutmut-cicd-stats.json`
- [x] 1.3 Para cada survivor, mapear a mutação concreta via diff `x_<func>__mutmut_orig` × `x_<func>__mutmut_N` nos `.py` de `mutants/src/`
- [x] 1.4 Classificar cada survivor como matável, equivalente ou já coberto (D3 do design)

## 2. Módulos de fechamento rápido

- [x] 2.1 Analisar e matar survivors de `application.use_cases` (2) — ambos equivalentes (tzinfo em `date().isoformat()`), registrados na lista de exceção
- [x] 2.2 Analisar e matar survivors de `application.formatting` (1) — assert exato de `format_evolution_csv` mata `lineterminator`
## 3. Camada de infraestrutura

- [x] 3.1 Matar survivors de `infrastructure.disk_cache` (42) em `tests/test_disk_cache.py` — 26 mortos, 16 equivalentes (encoding/`ensure_ascii`/`unlink(missing_ok)`)
- [x] 3.2 Matar survivors de `infrastructure.cached_client` (111) — novos testes em `test_disk_cache.py`
- [x] 3.3 Matar survivors de `infrastructure.b3_client` (80) — novo arquivo `tests/test_b3_client.py`

## 4. Camada de aplicação (analyze)

- [x] 4.1 Matar survivors de `application.analyze._texto` (60) — asserts exatos em `test_novo_resumo.py` (1 equivalente: `classificar_premio(_, None)`)
- [x] 4.2 Matar survivors de `application.analyze._evolucao` (63) — testes de fronteira em `test_evolucao_resumo.py` (14 equivalentes)
- [x] 4.3 Matar survivors de `application.analyze._resumo` (96) — novos testes de helpers internos
- [x] 4.4 Matar survivors de `application.analyze._texto_evolucao` (99) — asserts exatos e de conteúdo em `test_evolucao_resumo.py`

## 5. Camada de apresentação

- [x] 5.1 Matar survivors de `presentation.cli` (46) — novo arquivo `tests/test_cli.py` (1 equivalente)
- [x] 5.2 Matar survivors de `presentation.settings` (56) — novo arquivo `tests/test_settings.py` (2 equivalentes)
- [x] 5.3 Matar survivors de `presentation.charts` com lógica determinística (subconjunto dos 421, conforme corte definido) — 321 mortos (helpers determinísticos + render com asserts de layout); 100 visuais documentados em `docs/mutation-survivor-exceptions.md`
- [x] 5.4 Matar survivors de `infrastructure.desktop` (89) — testes em `test_b3_selic_pre.py` (3 equivalentes)

## 6. Documentação dos equivalentes

- [x] 6.1 Registrar os mutantes equivalentes numa lista de exceção com motivo da equivalência — `docs/mutation-survivor-exceptions.md`
- [x] 6.2 Confirmar que nenhum teste foi criado para equivalentes

## 7. Verificação final

- [x] 7.1 Rodar cada teste novo/modificado isoladamente (`pytest tests/<arquivo>::<classe>::<teste>`)
- [x] 7.2 Rodar `make lint` e corrigir qualquer violação apontada
- [x] 7.3 Rodar `make test` (cobertura >= 85%) e corrigir qualquer falha
- [x] 7.4 Confirmar que `mutmut` não foi executado em nenhuma etapa
