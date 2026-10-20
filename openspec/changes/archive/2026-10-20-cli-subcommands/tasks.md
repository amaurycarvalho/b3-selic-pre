## 1. Serviços headless de análise e exportação

- [x] 1.1 Adicionar `format_detailed_evolution_csv` em `application/formatting.py` com colunas `DATA;DU252;DC365;TAXA`, ordenação por data/dia útil e teste em `tests/test_application_services.py`.
- [x] 1.2 Criar `application/cli_services.py` com `ExportArtifact`, `build_analysis_text`, `build_evolution_text` e `build_export_artifacts`, sem imports de `presentation`/Tkinter, e testes headless correspondentes.
- [x] 1.3 Cobrir em teste a seleção de artefatos (`curva curta`, `curva longa`, `analise`, `log`) e o comportamento sem dados/histórico, garantindo que nenhum texto vazio seja produzido.
- [x] 1.4 Verificar que os textos usam `CurvaJurosConfig` montada a partir de mapping e que a suíte de arquitetura continua passando com `pytest tests/test_architecture.py -q`.

## 2. Estrutura de subcomandos da CLI

- [x] 2.1 Reescrever `presentation/cli.py` com parser raiz, subparsers `consultar`, `atualizar`, `exportar`, `gui` e `criar-atalho`, grupos de argumentos e teste de que `--help` lista os subcomandos.
- [x] 2.2 Implementar rejeição explícita da sintaxe antiga (data posicional, `--today`, `--yearly`, `--gui`, `--create-shortcut`) com código `2` e teste dos casos.
- [x] 2.3 Alterar `main` para retornar código de saída e ajustar `__main__.py` para encerrar com esse código; testar `0`, `1` e `2`.
- [x] 2.4 Implementar `--data` e `--no-cache` comuns aos comandos de dados, usando `default_reference_date`, `validate_query_date` e `nearest_business_day`; testar default, data inválida, futura, antiga e fim de semana.
- [x] 2.5 Implementar `consultar` com `--curva curta|longa|ambas`, incluindo cabeçalhos no modo `ambas`; testar os três modos e as colunas de cada CSV.
- [x] 2.6 Implementar `atualizar`, carregando data de referência e cinco datas históricas, gerando análise e evolução com a configuração persistida; testar saída normal, `--silencioso` e data histórica indisponível com client fake.
- [x] 2.7 Implementar `exportar` com `--curva`, `--analise`, `--log` e `--saida`; testar um artefato em stdout, vários artefatos em diretório temporário, nomes dos arquivos e erro `2` sem conteúdo ou com arquivo de saída inválido.
- [x] 2.8 Implementar `gui` e `criar-atalho`, mantendo `b3-selic-pre` sem argumentos abrindo a GUI; testar os três caminhos e a mensagem do atalho.
- [x] 2.9 Implementar `--version` e `--help` globais com código `0`; testar a saída de versão e a listagem de ajuda.

## 3. Logging de invocação e integração com a GUI

- [x] 3.1 Refatorar `presentation/gui/launch.py` para aceitar `Settings`/log já configurado e não chamar `configure_logging` quando a CLI já configurou; testar que a GUI não reconfigura o log.
- [x] 3.2 Adicionar helper `log_invocation` em `presentation/logging_utils.py` e envolver o despacho da CLI em `try/finally`; testar a presença de comando, argumentos, início, fim, duração e código em uma única linha INFO.
- [x] 3.3 Cobrir com testes as invocações `--help`, `--version`, erro de parsing, falha de comunicação, exceção não tratada, GUI sem argumentos e `gui`, verificando o código registrado.
- [x] 3.4 Garantir que a CLI use `Settings().log_retention_days()` ao configurar o log e que uma falha de logging não altere o código de saída; testar ambos.

## 4. Atalho, desktop e referências antigas

- [x] 4.1 Atualizar `infrastructure/desktop.py` para gerar `Exec=<executável> gui` e ajustar os testes de criação de atalho.
- [x] 4.2 Atualizar `b3-selic-pre.desktop` para `Exec=b3-selic-pre gui` e validar o conteúdo no teste correspondente.
- [x] 4.3 Remover ou atualizar referências a `--gui`, `--create-shortcut`, `--yearly` e data posicional em testes/docs que não sejam deltas históricos; executar `pytest tests/test_b3_selic_pre_gui.py tests/test_settings.py -q`.

## 5. Documentação

- [x] 5.1 Criar `docs/misc/cli.md` com sinopse, tabela de subcomandos, parâmetros, defaults, semântica de `--curva`, formatos de exportação, regras de `--saida`, validação de data, códigos de saída e formato do log.
- [x] 5.2 Adicionar ao `README.md` uma seção curta de linha de comando com exemplos e link para `docs/misc/cli.md`.
- [x] 5.3 Revisar `README.md` e demais docs para remover exemplos da sintaxe antiga (`--today`, `--yearly`, `--gui`, `--create-shortcut`).

## 6. Validação final

- [x] 6.1 Executar `make lint` e corrigir todas as falhas.
- [x] 6.2 Executar `make complexity` e corrigir violações introduzidas.
- [x] 6.3 Executar os testes diretamente afetados: `pytest tests/test_cli.py tests/test_application_services.py tests/test_logging.py tests/test_logging_utils.py -q`.
- [x] 6.4 Executar a suíte completa com `make test`, já que a mudança altera comportamento global de CLI, atalhos e logging.
- [x] 6.5 Fazer smoke test manual: `.venv/bin/python3 -m b3_selic_pre --help`, `consultar --data <data>`, `atualizar --silencioso`, `exportar --curva ambas --analise --saida /tmp/b3-export` e conferir o registro da invocação no log ativo.
