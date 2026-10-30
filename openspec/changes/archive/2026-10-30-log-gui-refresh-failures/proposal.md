# Proposal

## Why

Falhas de leitura de cache, de atualização e de fontes parciais nas sub-abas de dados da interface gráfica são hoje apenas convertidas em texto de status ou descartadas. O Tesouro Direto captura a exceção em `error` sem registrá-la; o worker da GUI a descarta; reservas e câmbio não registram falhas de fonte, pré-cálculo ou housekeeping. Isso dificulta o diagnóstico posterior. Esta change isola o registro em log, separando-o da mudança de feedback visual.

## What Changes

- Adicionar uma consulta pública `was_logged` em `presentation/logging_utils.py` para evitar registro duplicado da mesma exceção.
- Registrar falhas de leitura de cache e de atualização das sub-abas do Tesouro Direto, identificando a sub-aba e a operação.
- Registrar a falha tolerada de resgates do Tesouro sem interromper a atualização.
- Registrar falhas de fonte, pré-cálculo e housekeeping das Reservas Internacionais sem interromper a atualização.
- Registrar cada fonte de mercado que falhou e as falhas de pré-cálculo/housekeeping, mantendo `erros_fontes` e os dados disponíveis.
- Registrar nos workers da GUI apenas exceções que escapam do controller, usando `was_logged` para não duplicar.
- Manter a classificação existente: falhas de comunicação em uma linha, sem traceback; defeitos inesperados com traceback.
- Não alterar comportamento visual, cache, TTL, clientes HTTP nem payloads.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `application-logging`: falhas de atualização das sub-abas de dados da GUI, inclusive fontes parciais, passam a ser registradas no arquivo ativo, com classificação uniforme e sem registro duplicado.

## Impact

- `presentation/logging_utils.py`.
- `presentation/tesouro_analise_loading.py`, `presentation/tesouro_refresh.py`, `presentation/reserves_tab.py` e `presentation/market_refresh.py`.
- Workers de `presentation/gui/tesouro_sub_tab.py`, `presentation/gui/market_tab.py` e `presentation/gui/reserves_sub_tab.py`.
- Testes headless de logging e dos controllers de Tesouro, reservas e mercado.
- Sem novas dependências, mudanças de contrato de dados ou alterações no orçamento de testes de UI.
