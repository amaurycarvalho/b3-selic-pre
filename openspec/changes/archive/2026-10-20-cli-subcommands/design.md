## Context

Ver `proposal.md` para motivação. O estado atual relevante:

- `presentation/cli.py` usa um parser plano com data posicional e flags misturadas.
- `application/use_cases.py` já concentra validação de data, resolução da data de referência, consolidação anual e `build_export_text`.
- `application/formatting.py` já formata CSV bruto, consolidado e evolução consolidada; não existe CSV da evolução detalhada.
- `application/analyze` já expõe `analyze` e `analyze_evolution`, mas a CLI não os utiliza.
- `infrastructure/logging_setup.py` já oferece formato, rotação diária e retenção; a GUI usa retenção, a CLI não.
- `presentation/gui/launch.py` configura logging e monta seus próprios adapters, o que conflita com um registro de invocação da CLI que envolva a GUI.
- A camada `presentation` é o composition root permitido para a CLI; `application` não pode importar `presentation`, `infrastructure`, Tkinter ou matplotlib.

## Goals / Non-Goals

**Goals:**

- Uma única árvore de subcomandos, sem aliases da sintaxe antiga.
- Reutilizar validação, análise, evolução e formatação da camada `application`.
- Manter a CLI testável sem display e sem rede real.
- Registrar uma linha por invocação, inclusive GUI e erros de parsing.
- Manter o comportamento da GUI inalterado fora da forma de lançamento.

**Non-Goals:**

- Alterar a análise determinística, os limiares ou o formato dos textos existentes.
- Alterar o formato do log, a rotação diária ou a política de retenção padrão.
- Criar uma API HTTP, persistência de snapshots ou exportação para a área de transferência pela CLI.
- Manter compatibilidade com `b3-selic-pre <data>`, `--today`, `--yearly`, `--gui` ou `--create-shortcut`.

## Decisions

### 1. `argparse` com subparsers e despacho explícito

`main` criará um parser raiz com `subparsers`, cada subcomando com seu próprio parser e grupos de argumentos (`Dados`, `Saída`, `Execução`). O destino do subcomando será `comando`.

- Sem argumentos: `main` detecta `argv` vazio e despacha para `gui`.
- `gui`: subcomando explícito para atalhos e scripts.
- `consultar`, `atualizar`, `exportar`, `criar-atalho`: subcomandos de operação.
- `--help` e `--version`: argumentos globais do parser raiz.

Alternativa considerada: manter flags planas e adicionar `atualizar`/`exportar` como flags. Rejeitada porque perpetua a mistura de classes e não atende à organização por verbo.

### 2. `main` retorna código de saída e o entry point encerra o processo

`main(argv) -> int` concentra o despacho e devolve o código. O console script do `pyproject.toml` já faz `sys.exit(main())`; `__main__.py` passará a fazer `raise SystemExit(main())`.

Erros de uso e validação viram `2`; falhas de comunicação/dados viram `1`; sucesso, `--help` e `--version` viram `0`. Exceções inesperadas são registradas e relançadas, resultando em `1`.

Alternativa considerada: `main` levantar `SystemExit` em todos os caminhos. Rejeitada porque dificulta testes que verificam o código sem capturar exceção.

### 3. Data resolvida na aplicação, não no parser

O parser só valida o formato textual. A resolução usa os serviços existentes:

1. `default_reference_date()` quando `--data` é omitido;
2. `validate_query_date(data)` para formato, futuro e janela de 30 dias;
3. `nearest_business_day(data)` para ajustar fins de semana.

Isso mantém CLI e GUI alinhadas e evita duplicar regra de calendário. A janela de 30 dias é deliberada: é a mesma da GUI e cobre a janela de evolução de 28 dias.

### 4. `--curva` é a única seleção de representação

O parâmetro tem `choices=("curta", "longa", "ambas")`:

- `consultar`: `curta` = tabela bruta da data; `longa` = consolidado anual; `ambas` = duas seções no stdout.
- `exportar`: `curta` = CSV detalhado da janela de evolução; `longa` = CSV consolidado da janela; `ambas` = os dois artefatos.

`atualizar` não recebe `--curva`: a mesma carga histórica produz as duas representações e os dois textos.

Alternativa considerada: manter `--visao` para `consultar` e `--evolucao` para `exportar`. Rejeitada por duplicar conceito e contrariar a decisão de um seletor único.

### 5. Serviços headless para análise e exportação

Novo módulo `application/cli_services.py` (nome provisório, a confirmar na implementação) com responsabilidades puras:

- `build_analysis_text(records, config) -> str`;
- `build_evolution_text(current, previous, config) -> str | None`;
- `build_export_artifacts(...) -> list[ExportArtifact]`, com `ExportArtifact(name, content)`.

`application/formatting.py` ganha `format_detailed_evolution_csv(historical_data)` com colunas `DATA;DU252;DC365;TAXA`.

A CLI apenas seleciona artefatos e grava. A aplicação não conhece stdout, diretórios ou nomes de arquivo.

Alternativa considerada: montar textos diretamente em `presentation/cli.py`. Rejeitada porque a GUI também consome os mesmos textos e a regra ficaria duplicada.

### 6. `atualizar` como orquestração de composition root

O fluxo será:

1. resolver a data;
2. `CachedB3Client.fetch_rates_for_date(data, force=no_cache)`;
3. `CachedB3Client.fetch_historical_rates(data, force=no_cache)`;
4. `analyze(records, historical_data=historical, config=config)`;
5. escolher a data anterior mais recente com registros e chamar `analyze_evolution` + `montar_evolucao_resumo`;
6. imprimir os blocos, salvo `--silencioso`.

A configuração vem de `Settings` e é convertida com `CurvaJurosConfig.from_mapping`, como na GUI. Datas históricas vazias são omitidas da análise e reportadas no texto/status.

### 7. `exportar` com modelo de artefatos e regra de destino

A seleção é combinável:

- `--curva` adiciona um ou dois CSVs;
- `--analise` adiciona um texto;
- `--log` adiciona uma cópia do log ativo.

Regra de destino:

- exatamente um artefato e `--saida` omitido: stdout;
- mais de um artefato: `--saida` deve ser diretório; arquivos são gravados com nomes fixos (`curva-curta.csv`, `curva-longa.csv`, `analise.txt`, `b3-selic-pre.log`);
- `--saida` arquivo com mais de um artefato: erro de uso `2`.

Arquivos existentes com o mesmo nome serão sobrescritos, para tornar a exportação idempotente. O diretório é criado se não existir.

Alternativa considerada: concatenar tudo no stdout com separadores. Rejeitada porque quebra o consumo por planilhas e scripts.

### 8. Log de invocação único no `finally`

`main` configura o logging uma vez, com `retention_days=Settings().log_retention_days()`, e instala os hooks. Em seguida:

```text
t0 = monotonic()
inicio = agora local em ISO 8601
try:
    codigo = dispatch(...)
except SystemExit as exc:
    codigo = normalizar(exc.code)
except Exception:
    codigo = 1
    raise
finally:
    log_invocation(comando, argumentos, inicio, agora, monotonic() - t0, codigo)
```

O helper `log_invocation` fica em `presentation/logging_utils.py`, grava uma única linha INFO com campos `comando`, `argumentos`, `inicio`, `fim`, `duracao` e `codigo_saida`, e não levanta exceção se o logging falhar.

Para `gui` e execução sem argumentos, `launch_gui` recebe `settings` e `active_log` já configurados e NÃO chama `configure_logging` novamente. A duração cobre toda a sessão da janela.

### 9. Ajustes de atalho e desktop

`infrastructure/desktop.py` passa a montar `Exec=<executável> gui`; o `.desktop` versionado no repositório usa `Exec=b3-selic-pre gui`.

### 10. Documentação como parte da entrega

`docs/misc/cli.md` documenta comandos, parâmetros, defaults, semântica de `--curva`, formatos, códigos de saída, regras de `--saida`, validação de data e logging. O `README.md` ganha uma seção curta com exemplos e link para esse arquivo.

## Risks / Trade-offs

- [GUI reconfigurando o log e perdendo o registro da CLI] → `main` configura uma vez e `launch_gui` recebe o estado; teste dedicado para chamada sem reconfiguração.
- [Snapshot do log não incluir a invocação atual] → comportamento documentado em `cli.md`; o registro é escrito no `finally`, depois da exportação.
- [`--curva ambas` em `consultar` produzir saída não trivial para pipes] → cabeçalhos explícitos e documentação; `exportar` é o caminho recomendado para consumo por máquina.
- [Janela de 30 dias bloquear consultas antigas] → mesma regra da GUI; documentar e manter a mensagem de validação existente.
- [Datas históricas ausentes gerarem análise parcial] → omitir datas vazias, reportar indisponibilidade e manter o código `0` quando a data base existe.
- [Reescrita ampla de `tests/test_cli.py`] → separar testes de parsing, dispatch, exportação e logging; usar mocks de infraestrutura e serviços headless reais.
- [Specs antigas citando flags removidas] → deltas para `yearly-consolidation`, `shortcut-installer`, `desktop-entry` e `app-icon`.

## Migration Plan

1. Implementar serviços headless e formatação detalhada, com testes.
2. Reescrever a CLI com subparsers, despacho, validação e logging de invocação.
3. Refatorar `launch_gui` para receber logging já configurado.
4. Atualizar `infrastructure/desktop.py` e `b3-selic-pre.desktop`.
5. Atualizar `tests/test_cli.py`, testes de desktop e documentação.
6. Executar `make lint`, `make complexity` e a suíte completa, dado que a mudança altera comportamento global de CLI e atalhos.

Rollback: reverter o change e restaurar o parser/flag antigos e os manifestos de atalho; não há migração de dados persistidos.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
