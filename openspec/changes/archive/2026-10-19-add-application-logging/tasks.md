## 1. Fundação

- [x] 1.1 Criar `application/errors.py` com `CommunicationError` e verificar a importação em um teste headless novo (`pytest tests/test_application_errors.py`).
- [x] 1.2 Criar `infrastructure/xdg.py` com `cache_base()` e refatorar `disk_cache._xdg_cache_dir` para usá-lo; verificar com `pytest tests/test_disk_cache.py` e com testes novos de caminho Linux/XDG/Windows/macOS.
- [x] 1.3 Adicionar `log_retention_days: 7` a `DEFAULT_SETTINGS` e o getter validado `Settings.log_retention_days()`; verificar com `pytest tests/test_settings.py`, cobrindo ausente, inteiro válido, string, float, booleano, `null` e valor menor que `1`.

## 2. Núcleo de logging

- [x] 2.1 Implementar `infrastructure/logging_setup.py` com resolução do diretório de logs, rotação de startup, anexação em colisão, retenção, handler diário e `configure_logging` usando `basicConfig(format=..., datefmt=..., handlers=[...], force=True)`; verificar criando `tests/test_logging.py` e executando `pytest tests/test_logging.py`.
- [x] 2.2 Cobrir rotação em `tests/test_logging.py`: arquivo ausente, arquivo do dia corrente, arquivo antigo, destino já existente, data usada da última modificação e garantia de que o ativo não é apagado; verificar com `pytest tests/test_logging.py`.
- [x] 2.3 Cobrir retenção em `tests/test_logging.py`: cutoff `hoje - N`, preservação de hoje e dos `N` dias anteriores, remoção apenas de `b3-selic-pre-YYYY-MM-DD.log`, preservação de nomes fora do padrão e tratamento de `N` gigante; verificar com `pytest tests/test_logging.py`.
- [x] 2.4 Verificar formato e rotação nomeada: o handler deve produzir `b3-selic-pre-YYYY-MM-DD.log` na virada e toda linha deve conter timestamp local `YYYY-MM-DD HH:MM:SS`; adicionar teste em `tests/test_logging.py` e executar `pytest tests/test_logging.py`.

## 3. Falhas de comunicação

- [x] 3.1 Adicionar a tupla de exceções de rede em `infrastructure/b3_client.py` e o wrapper de `CommunicationError` nos métodos públicos de fetch de `infrastructure/cached_client.py`; verificar com testes novos para `URLError`, `HTTPException`, `TimeoutError` e `ConnectionError`, e para `ValueError`/`OSError` não classificados como comunicação (`pytest tests/test_disk_cache.py`).
- [x] 3.2 Implementar `presentation/logging_utils.py` com `is_communication_error`, `log_exception`, `install_exception_hooks` e `install_tk_exception_hook`; verificar com testes headless para causa/contexto, ciclo de causas, linha única, normalização de newlines, traceback para não-comunicação e instalação dos hooks com fakes (`pytest tests/test_logging_utils.py`).

## 4. Integração com CLI e GUI

- [x] 4.1 Atualizar os dois workers de `presentation/gui/fetch.py` para capturar `Exception`, chamar `log_exception` dentro do `except` e agendar a atualização da UI em `finally`; verificar executando os testes de GUI existentes e um teste manual de falha de rede na GUI.
- [x] 4.2 Atualizar `presentation/gui/launch.py` para criar `Settings` uma vez, configurar logging com retenção, instalar os hooks, registrar a linha INFO de início e passar o mesmo `Settings` para `GuiDependencies`; verificar por teste manual de inicialização, presença da linha INFO e remoção de backups antigos.
- [x] 4.3 Atualizar `presentation/cli.py` para configurar logging nos caminhos de busca, registrar a linha INFO, tratar falha de comunicação com mensagem em stderr e `SystemExit(1)`, e relançar não-comunicação após o traceback; verificar com testes novos em `tests/test_cli.py` para os dois caminhos e para a linha de início.

## 5. Validação

- [x] 5.1 Rodar `make lint`, `make complexity` e `make test`; corrigir qualquer falha e confirmar cobertura mínima de 85%.
- [x] 5.2 Executar verificação manual: simular arquivo ativo com mtime de ontem e iniciar a GUI (rotação), criar backups datados e ajustar `log_retention_days` (retenção), provocar falha de rede na CLI (linha única + exit 1) e uma exceção de programação (traceback completo no log).
