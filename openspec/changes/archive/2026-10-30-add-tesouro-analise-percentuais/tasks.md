# Tasks

## 1. Pré-requisitos e ajustes de planejamento (concluído)

- [x] 1.1 Ajuste aplicado: `add-tesouro-direto-vendas` não entrega mais GUI (botão/janela Toplevel) e mantém dados + CLI; a spec `tesouro-direto-gui` foi removida.
- [x] 1.2 Ajuste aplicado: `add-tesouro-direto-resgates-estoque` não entrega mais abas de GUI e mantém dados + CLI; a spec `tesouro-resgates-estoque-gui` foi removida.
- [x] 1.3 Ajuste aplicado: as specs de cache bruto das duas changes pré-requisitas usam TTL condicional (1 h corrente, 6 h histórico, 24 h mensal/eventual) e mantêm o raw cumulativo sem poda.
- [x] 1.4 Ajuste verificado: `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` continuam válidas; restam apenas avisos pré-existentes de requisitos longos.

## 2. Taxonomia e percentuais

- [x] 2.1 Criar o registry de indexadores em `application/tesouro/` com `SELIC`, `SELIC_RESERVA`, `IPCA`, `PREFIXADO`, `IGP-M` e `OUTROS`; verificar com teste que todos os títulos atuais são classificados.
- [x] 2.2 Implementar `classificar_familia(tipo_titulo)` puro, com normalização de caixa/acentos e fallback `OUTROS` + aviso; verificar teste com título desconhecido.
- [x] 2.3 Implementar a composição percentual do estoque por família e por título, por valor, no último mês; verificar testes de soma 100%, base valor e total zero.
- [x] 2.4 Implementar o percentual de demanda por família e por título para 14d/3m/12m/3a, ancorado na maior data disponível; verificar testes de janela, base valor e janela vazia.
- [x] 2.5 Implementar o fluxo líquido (vendas − recompras) por família/título/janela, sem vencimentos/cupons; verificar testes de fluxo positivo, negativo e exclusão de eventos contratuais.
- [x] 2.6 Documentar a semântica de “valor” (metodologia do Tesouro, não mercado) e “quantidade secundária” em `docs/misc/datasources.md`; verificar que o texto cita explicitamente a ressalva.

## 3. Contrato de séries

- [x] 3.1 Adicionar os tipos imutáveis `SeriesKey`/`SeriesPoint` no domínio ou em `application/tesouro/`; verificar teste de imutabilidade e campos.
- [x] 3.2 Implementar o `SeriesProvider` do Tesouro para dimensões família/produto/produto+vencimento e métricas de estoque/demanda/fluxo; verificar teste de contrato com um provider fake.
- [x] 3.3 Implementar os buckets diário/semanal/mensal e a regra de estoque sempre mensal; verificar testes de 14d diário, 3m semanal, 12m/3a mensal.
- [x] 3.4 Implementar o tratamento de ciclo de vida de título (zero/lacuna explícita) e a ausência de períodos futuros; verificar testes de título que aparece/desaparece e de janela sem dados.
- [x] 3.5 Garantir que `application` não importa `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede; verificar com `tests/test_architecture.py` e teste de importação headless.

## 4. Cache analítico e TTL

- [x] 4.1 Implementar `tesouro_analytics_cache.py` com layout `analytics/`, manifest e escrita atômica; verificar teste de gravação/leitura e de leitor concorrente sem conteúdo parcial.
- [x] 4.2 Implementar invalidação por `sha256`/`latest_data_date` e recálculo das partições afetadas; verificar teste de fonte alterada.
- [x] 4.3 Implementar housekeeping de 3 anos ancorado no `latest_data_date`, com corte de 36 meses para séries mensais e a mesma data para diárias/semanais; verificar teste com fonte atrasada.
- [x] 4.4 Garantir leitura somente leitura sem remover, renomear ou alterar arquivos; verificar teste de cache corrompido/vencido em modo read-only.
- [x] 4.5 Implementar o wrapper de TTL do raw (1 h corrente, 6 h histórico, 24 h mensal/eventual) e o reaproveitamento em `304`; verificar testes de TTL e `304`.
- [x] 4.6 Integrar `ActionLock` dedicado para analytics e documentar a concorrência CLI/GUI; verificar teste de lock ou de composição do caminho.

## 5. Health check e erros

- [x] 5.1 Implementar `tesouro_source_health.py` validando `success`, recurso CSV, cabeçalho e mês consolidado; verificar testes de fonte saudável, ausente e schema alterado.
- [x] 5.2 Implementar o aviso de defasagem mensal > 3 meses e a mensagem de “último mês consolidado”; verificar teste com fonte atrasada.
- [x] 5.3 Garantir que falha de saúde levanta `TesouroDataError` sem fallback ou scraping; verificar teste de ausência de fonte alternativa.
- [x] 5.4 Garantir classificação `CommunicationError` para rede/HTTP/timeout/parcial e logging de uma linha; verificar teste de log e tipo de erro.

## 6. Integração e validação

- [x] 6.1 Expor a API pública de análise (taxonomia, percentuais, fluxo, séries) em `application/tesouro/__init__.py`; verificar teste de importação headless.
- [x] 6.2 Rodar `make lint` e `make complexity`; corrigir violações.
- [x] 6.3 Rodar a suíte completa `make test` (justificada por cache, taxonomia e contratos compartilhados) e registrar o resultado.
- [x] 6.4 Registrar um teste manual opcional: gerar percentuais de estoque/demanda a partir de um cache real e conferir a soma 100% e o fluxo líquido.

## Workflow follow-up

- Revisar a change com o usuário e arquivar após a aprovação.
- Só então criar/aplicar `add-tesouro-gui`, que consumirá esta API.
