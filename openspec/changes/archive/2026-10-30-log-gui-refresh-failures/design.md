# Design

## Context

Ver `proposal.md` para a motivação. O helper `presentation/logging_utils.log_exception` já classifica falhas de comunicação (uma linha, sem traceback) e demais exceções (com traceback), marcando a exceção para evitar re-registro por hooks. Hoje:

- `TesouroLoadingMixin.load` captura a exceção e grava apenas `error`/`error_context`.
- `tesouro_refresh._refresh_appetite` ignora a falha de resgates.
- `ReservesTabController._fetch` acumula a falha em `erros_fontes`; `_store_artifact` e o housekeeping descartam exceções.
- `market_refresh` acumula falhas por fonte em `erros_fontes` e descarta falhas de pré-cálculo/housekeeping.
- Os workers da GUI convertem a exceção em texto de status, sem log.

## Goals / Non-Goals

**Goals:**

- Registrar falhas de cache, atualização e fontes parciais no arquivo ativo, com contexto da sub-aba/operação.
- Manter a classificação existente de comunicação versus defeito inesperado.
- Garantir um único registro por exceção mesmo quando ela atravessa controller e GUI.
- Cobrir o comportamento com testes headless de `caplog`, sem aumentar o orçamento de UI.

**Non-Goals:**

- Alterar mensagens da statusbar, o fluxo de carregamento ou a interface visual.
- Alterar cache, TTL, clientes HTTP, payloads ou regras de negócio.
- Registrar eventos de sucesso ou métricas de desempenho.

## Decisions

### 1. `was_logged` público em `presentation/logging_utils.py`

Expor `was_logged(exc)` reutilizando o marcador `_b3_selic_logged` já aplicado por `log_exception`. O limite superior consulta esse marcador antes de registrar, permitindo que controllers e GUI compartilhem a regra “uma vez por exceção” sem duplicar a implementação.

Alternativa rejeitada: remover o marcador e confiar apenas no fluxo de exceções. Como os controllers capturam e não relançam, o mesmo erro poderia ser registrado novamente em um limite diferente.

### 2. Log no limite que trata a exceção

- `TesouroLoadingMixin.load`: registrar antes de gravar `error`, com contexto `Falha ao ler o cache do Tesouro Direto (<kind>)` ou `Falha ao atualizar o Tesouro Direto (<kind>)`.
- `tesouro_refresh._refresh_appetite`: registrar a falha tolerada de resgates e continuar com `redemptions = []`.
- `ReservesTabController._fetch`: registrar a falha da fonte e ainda devolver `erros_fontes`; `_store_artifact` e o housekeeping registram falhas não fatais.
- `market_refresh`: registrar cada fonte que falhou (`BCB SGS 1`, `B3`, `B3 DOL`, `BCB Focus`, `Yahoo GC=F`) e as falhas de cache derivado/pré-cálculo/housekeeping.
- Workers da GUI: registrar apenas exceções que escapam do controller, com contexto da sub-aba.

Alternativa rejeitada: registrar apenas na GUI. Isso perderia falhas parciais tratadas dentro dos controllers e impediria testes headless do comportamento.

### 3. Falhas parciais continuam não fatais

Uma falha de fonte, pré-cálculo ou housekeeping continua sendo acumulada em `erros_fontes` ou ignorada no fluxo principal; o log é adicional e não altera o resultado entregue ao usuário. Falhas de comunicação continuam em linha única; defeitos inesperados mantêm o traceback.

Alternativa rejeitada: relançar falhas parciais para que o worker da GUI as registre. Isso interromperia atualizações que hoje preservam dados disponíveis.

## Risks / Trade-offs

- [Log de falhas parciais pode poluir o arquivo] → usar contexto curto e específico por fonte, no nível já usado para falhas toleradas.
- [Duplicação de registro entre controller e GUI] → `was_logged` no limite superior e marcador compartilhado.
- [Mudança de comportamento em caso de falha de pré-cálculo] → registrar e manter o fluxo atual, sem propagar a exceção.
- [Testes dependentes de mensagens exatas] → verificar por contexto/fonte e presença de traceback, não pela linha inteira.

## Migration Plan

Não há migração de dados. A mudança só acrescenta registros de log; reverter significa remover as chamadas de log e o helper `was_logged`.
