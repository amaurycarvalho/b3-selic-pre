## 1. Defaults de primeira execução

- [x] 1.1 Em `src/b3_selic_pre/presentation/settings.py`, detectar a ausência do arquivo no construtor e separar `DEFAULT_SETTINGS` (compatibilidade) de `FIRST_RUN_DEFAULTS` (`view_mode="consolidated"`, `evolution=True`, `sidebar=True`), aplicando os defaults de primeira execução apenas quando o arquivo não existir; verificar com `pytest tests/test_settings.py`.
- [x] 1.2 Manter a persistência preguiçosa: não gravar arquivo no construtor e garantir que o primeiro `set()` persista os defaults de primeira execução já aplicados; verificar com teste headless de persistência.

## 2. Testes

- [x] 2.1 Atualizar `tests/test_settings.py` para cobrir: arquivo ausente → `consolidated`, evolução ligada, análise ligada e 3D desligado; arquivo válido sem uma chave → defaults de compatibilidade (`raw`/off/off); JSON inválido ou não-objeto → compatibilidade; verificar com `pytest tests/test_settings.py`.
- [x] 2.2 Adicionar teste garantindo que um arquivo existente com preferências gravadas continua prevalecendo sobre os defaults de primeira execução; verificar com `pytest tests/test_settings.py`.

## 3. Verificação da GUI

- [x] 3.1 Com `XDG_CONFIG_HOME` apontando para um diretório temporário vazio, iniciar a GUI e confirmar que "Curva longa", "Evolução da curva" e "Análise" aparecem marcados, enquanto "3D" permanece desmarcado e a mensagem inicial da barra de status é exibida; verificar manualmente sob `xvfb-run`.
- [x] 3.2 Reiniciar a GUI com um `settings.json` existente contendo preferências diferentes e confirmar que essas preferências prevalecem (sem reaplicar os defaults de primeira execução); verificar manualmente sob `xvfb-run`.

## 4. Qualidade e validação

- [x] 4.1 Executar `make lint` e corrigir eventuais violações.
- [x] 4.2 Executar `make complexity` e corrigir eventuais violações de complexidade.
- [x] 4.3 Executar os testes diretamente relacionados: `pytest tests/test_settings.py tests/test_architecture.py tests/test_ui_test_budget.py`.
- [x] 4.4 Executar `make test` por se tratar de comportamento global de inicialização da GUI.
- [x] 4.5 Executar `openspec validate set-first-run-defaults --strict` e corrigir eventuais problemas dos artefatos.
