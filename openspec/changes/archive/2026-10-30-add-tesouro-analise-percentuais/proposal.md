## Why

As changes `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` entregam dados brutos de vendas, resgates e estoque, mas o objetivo analítico do produto é responder, em percentual, **qual a composição do estoque por indexador** (SELIC, IPCA, Prefixado, IGP-M) e **qual o apetite do mercado por título**. Sem uma camada derivada, esses números só existem se o usuário somar e normalizar manualmente os CSVs.

Esta change cria essa camada: taxonomia de indexadores, percentuais de estoque e demanda, fluxo líquido, séries temporais normalizadas e cache analítico com retenção de 3 anos. Ela é headless e não altera a GUI; a aba “Tesouro Direto” é tratada em `add-tesouro-gui`.

## What Changes

- Adicionar a capability `tesouro-analise` para classificar títulos por família de indexador e calcular percentuais normalizados.
- Classificar `Tesouro Reserva` como SELIC (subfamília `SELIC_RESERVA`, somada em SELIC no headline).
- Calcular composição do estoque por valor: `% = valor_estoque(família/título) / valor_estoque(total do mês)`.
- Calcular apetite do mercado por valor: `% = valor(vendas) / valor(total da janela)`, com janelas de 14 dias, 3 meses, 12 meses e 3 anos.
- Calcular fluxo líquido por título/família: vendas menos recompras antecipadas; vencimentos e cupons ficam fora do apetite.
- Oferecer séries temporais normalizadas por família, produto e produto+vencimento, com buckets diário, semanal e mensal.
- Adicionar cache analítico em `.../b3-selic-pre/tesouro/analytics/`, com retenção de 3 anos e housekeeping ancorado no `latest_data_date`.
- Manter o cache bruto cumulativo completo; aplicar TTL condicional: 1 h para vendas/recompras quando o cache contém o dia corrente, 6 h para histórico, 24 h para estoque/cupom/vencimentos.
- Adicionar health check da fonte de estoque: validar dataset, recurso CSV, cabeçalho e mês consolidado; falhar com `TesouroDataError` se a fonte mudar ou sumir.
- Expor uma API headless de séries (`SeriesPoint`/`SeriesProvider`) reutilizável pela futura change de câmbio.
- **Dependência:** requer `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` implementadas antes da aplicação.
- **Non-goals:** GUI, gráficos, abas, CLI de análise, projeções futuras, câmbio, ouro, dados por investidor, banco de dados, agendamento.

## Capabilities

### New Capabilities

- `tesouro-analise`: taxonomia de indexadores, composição percentual do estoque, apetite percentual do mercado, fluxo líquido, séries temporais normalizadas, cache analítico de 3 anos, health check da fonte e contrato headless de séries.

### Modified Capabilities

<!-- Nenhuma capability principal é alterada por esta change; ela consome os deltas das changes pré-requisitas. -->

## Impact

- Novos módulos em `src/b3_selic_pre/application/tesouro/` para taxonomia, percentuais, fluxo líquido e séries.
- Novo módulo de cache analítico em `src/b3_selic_pre/infrastructure/tesouro_analytics_cache.py`.
- Novo health check em `src/b3_selic_pre/infrastructure/tesouro_source_health.py`.
- Possível extensão de `domain/models.py` com tipos de série imutáveis; nenhum modelo bruto é alterado.
- Testes headless de taxonomia, percentuais, fluxo líquido, séries, TTL, housekeeping e health check.
- Nenhuma dependência externa nova.
- A suíte completa é justificada por envolver contratos compartilhados de cache, taxonomia e séries que serão usados pela GUI e pelo câmbio futuro.
- As changes pré-requisitas já foram ajustadas no planejamento para remover a GUI e alinhar o TTL do cache bruto.
