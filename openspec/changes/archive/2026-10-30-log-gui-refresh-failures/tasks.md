# Tasks

## 1. Helper de exceção já registrada

- [x] 1.1 Expor em `presentation/logging_utils.py` uma consulta pública `was_logged(exc)` reutilizando o marcador existente de `log_exception`; verificar em `tests/test_logging_utils.py` que uma exceção marcada é reconhecida, que uma não marcada é rejeitada e que o comportamento atual de `log_exception` permanece.

## 2. Falhas do Tesouro Direto

- [x] 2.1 Em `presentation/tesouro_analise_loading.py`, registrar a exceção de `load` com contexto da sub-aba e da operação (`ler o cache`/`atualizar`) antes de guardar `error`; verificar com `caplog` em `tests/test_tesouro_analise_controller.py` para falha de cache e de atualização.
- [x] 2.2 Em `presentation/tesouro_refresh.py`, registrar a falha tolerada de resgates sem interromper a atualização; verificar com `caplog` em `tests/test_tesouro_loaders.py` ou novo teste headless de refresh.

## 3. Falhas de Reservas e Mercado

- [x] 3.1 Em `presentation/reserves_tab.py`, registrar falhas da fonte, do pré-cálculo e do housekeeping sem interromper a atualização; verificar com `caplog` em `tests/test_reserves_presentation.py`.
- [x] 3.2 Em `presentation/market_refresh.py`, registrar cada fonte de mercado que falhou e as falhas de pré-cálculo/housekeeping, mantendo `erros_fontes` e os dados disponíveis; verificar com `caplog` em `tests/test_market_presentation.py`.

## 4. Workers da GUI e classificação

- [x] 4.1 Nos workers de `presentation/gui/tesouro_sub_tab.py`, `presentation/gui/market_tab.py` e `presentation/gui/reserves_sub_tab.py`, registrar apenas exceções que escapam do controller, usando `was_logged` para não duplicar; verificar com revisão estática e teste manual provocando falha no `Atualizar`.
- [x] 4.2 Confirmar em teste headless que falha de comunicação gera uma linha sem traceback e defeito inesperado mantém o traceback no log; verificar em `tests/test_logging_utils.py` e nos testes de `caplog` dos controllers.

## 5. Validação

- [x] 5.1 Executar `make lint` e verificar que termina sem erros.
- [x] 5.2 Executar `make complexity` e verificar que termina sem violações.
- [x] 5.3 Executar `python -m pytest tests/test_logging_utils.py tests/test_tesouro_analise_controller.py tests/test_tesouro_loaders.py tests/test_reserves_presentation.py tests/test_market_presentation.py -q` e verificar que todos passam.
- [x] 5.4 Executar `make test` porque a mudança toca logging compartilhado e pode causar regressões na suíte inteira.
- [x] 5.5 Teste manual opcional: provocar falha no `Atualizar` do Tesouro, de Dólar e Ouro e de Reservas Internacionais e confirmar o registro correspondente no log ativo e a mensagem na statusbar.
