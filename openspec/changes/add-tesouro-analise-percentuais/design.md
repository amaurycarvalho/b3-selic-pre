## Context

As changes `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` criam a ingestão, o cache bruto e os modelos de vendas, resgates e estoque. Esta change consome esses dados para produzir percentuais e séries, sem GUI.

O projeto já tem:

- Clean Architecture com guardas em `tests/test_architecture.py`;
- `Decimal` para valores monetários;
- cache em disco com escrita atômica (`cache_payload.write_atomic`) e leitura somente leitura (`DiskCache`);
- `ActionLock` para concorrência;
- `CommunicationError` e o padrão de logging de uma linha;
- `xdg.cache_base()` para o diretório de cache.

O spike confirmou: vendas/recompras diárias com defasagem de até dois dias úteis; estoque mensal com divulgação no primeiro dia do segundo mês subsequente; `Tesouro Reserva` é 100% Selic e entrou em 2026; a composição por quantidade é distorcida por PU, então a base deve ser valor.

## Goals / Non-Goals

**Goals:**

- Produzir percentual de estoque por família e por título, por valor, no último mês consolidado.
- Produzir percentual de demanda (vendas) por família e por título, por valor, em 14d/3m/12m/3a.
- Produzir fluxo líquido (vendas − recompras) por família/título/janela.
- Produzir séries temporais normalizadas, com buckets diário/semanal/mensal e dimensões família/produto/produto+vencimento.
- Manter cache analítico de 3 anos, com housekeeping ancorado no `latest_data_date`.
- Manter o contrato de séries genérico para a futura change de câmbio.
- Validar a fonte de estoque e falhar de forma clara se ela mudar.

**Non-Goals:**

- GUI, abas, gráficos e lazy rendering; ficam em `add-tesouro-gui`.
- CLI de análise; as tabelas brutas continuam na CLI das changes pré-requisitas.
- Projeções futuras, modelos preditivos ou cenários de política.
- Câmbio, dólar, ouro e correlações macro.
- Dados por investidor (`operacoes-do-tesouro-direto`).
- Banco de dados, agendamento e exportação dedicada.
- Alterar os modelos brutos de vendas, resgates ou estoque.

## Decisions

### 1. Taxonomia em `application`, não no modelo bruto

**Decisão:** manter `tipo_titulo` como veio do CSV e derivar `familia_indice`/`subfamilia` por uma função pura em `application/tesouro/`.

Registry inicial:

| `tipo_titulo` | Família | Subfamília |
| --- | --- | --- |
| Tesouro Selic | SELIC | SELIC |
| Tesouro Reserva | SELIC | SELIC_RESERVA |
| Tesouro IPCA+ | IPCA | IPCA |
| Tesouro IPCA+ com Juros Semestrais | IPCA | IPCA_JUROS |
| Tesouro RendA+ | IPCA | RENDA |
| Tesouro Educa+ | IPCA | EDUCA |
| Tesouro Prefixado | PREFIXADO | PREFIXADO |
| Tesouro Prefixado com Juros Semestrais | PREFIXADO | PREFIXADO_JUROS |
| Tesouro IGPM+ com Juros Semestrais | IGP-M | IGP_M |
| desconhecido | OUTROS | OUTROS |

- `Tesouro Reserva` é somado em SELIC no headline e mantido como subfamília para não distorcer o prazo médio.
- Título desconhecido não é descartado; vira `OUTROS` e gera aviso.
- O registry é data-driven e coberto por teste para cada título conhecido e para um título novo.

**Alternativa rejeitada:** gravar a família no CSV/cache bruto. Isso envelheceria a classificação e exigiria reescrever o cache quando um título novo aparecesse.

### 2. Percentuais por valor, com quantidade como visão secundária

**Decisão:** usar `Valor Estoque` e `Valor` como base dos percentuais.

- Estoque: `valor_estoque(título/família) / total do mês`.
- Demanda: `valor(vendas do título/família na janela) / total da janela`.
- Quantidade fica disponível como métrica secundária, nunca como headline.

**Racional:** o PU varia muito entre produtos; `Tesouro Reserva` tem PU ~10 contra ~1.000 dos demais. Em quantidade, ele domina a demanda, mas em valor representa uma fração. Para “apetite” e “exposição”, valor é a base comparável.

**Trade-off:** `Valor Estoque` não é valor de mercado; é o valor na metodologia do Tesouro (juros acumulados pela taxa de emissão). O rótulo e a documentação devem deixar isso explícito.

### 3. Janelas ancoradas no último dado, não no relógio

**Decisão:** 14d, 3m, 12m e 3a são calculados a partir da maior data disponível no dataset.

- Estoque: último mês consolidado; nunca diário.
- Vendas/recompras: última `data_liquidacao`/`data_resgate`.
- Fluxo líquido: mesma janela de vendas e recompras.

**Racional:** a fonte tem defasagem. Usar `hoje` produziria janelas vazias ou parciais.

### 4. Fluxo líquido separado do apetite

**Decisão:** o headline “apetite” é o share de vendas; o fluxo líquido é uma série separada.

`fluxo_liquido = vendas − recompras antecipadas`; vencimentos e cupons não entram.

**Racional:** vendas medem demanda bruta; recompras medem saída antecipada. Vencimentos e cupons são contratuais e não refletem escolha do investidor. O fluxo líquido pode ser negativo e deve ser exibido como valor, não como percentual.

### 5. Contrato de séries genérico

**Decisão:** introduzir tipos imutáveis em `application`:

```text
SeriesKey(dimension, key)
SeriesPoint(period, metric, value, total, dimension, key)
SeriesProvider.fetch(key, start, end, bucket) -> list[SeriesPoint]
```

- `dimension`: `familia`, `produto`, `produto_vencimento`.
- `metric`: `estoque_pct`, `demanda_pct`, `fluxo_liquido`, `estoque_valor`, `demanda_valor`.
- `period`: `AAAA-MM-DD` para diário/semanal, `AAAA-MM` para mensal.
- `bucket`: `diario`, `semanal`, `mensal`.

A futura change de câmbio implementa o mesmo `SeriesProvider` com `dimension="macro"` e `key="USD_BRL"`/`OURO`, sem alterar o cálculo do Tesouro.

**Alternativa rejeitada:** funções específicas por gráfico. Acoplariam a análise ao matplotlib e dificultariam o câmbio.

### 6. Cache analítico em duas camadas

**Decisão:** manter o cache bruto cumulativo e criar um cache analítico derivado.

```text
$XDG_CACHE_HOME/b3-selic-pre/tesouro/
+-- raw/                         # cumulativo, completo, sem poda
|   +-- vendas.csv + .metadata.json
|   +-- estoque.csv + .metadata.json
|   +-- recompras.csv + .metadata.json
|   +-- cupom.csv + .metadata.json
|   +-- vencimentos.csv + .metadata.json
+-- analytics/
|   +-- manifest.json            # versao, hashes, latest_data_date
|   +-- composicao-estoque/      # particoes mensais
|   +-- demanda-vendas/          # diario/ semanal/ mensal/
|   +-- fluxo-liquido/
+-- locks/
```

- O raw não é podado: ~15 MB no total e preserva revisões.
- O analytics retém 3 anos.
- `manifest.json` guarda `schema_version`, `source_sha256` por recurso, `latest_data_date` e a versão do registry.
- Invalidação: se o hash ou `latest_data_date` mudar, as partições afetadas são recalculadas.
- Housekeeping: após refresh bem-sucedido, remove partições anteriores a `latest_data_date - 3 anos`. Para séries mensais, manter 36 meses; para diárias/semanais, o corte é a mesma data.
- Escrita atômica: `write_atomic_bytes` para CSV e `write_atomic` para JSON; manifest por último.
- Leitura somente leitura não apaga nem renomeia.

**Alternativa rejeitada:** podar o CSV bruto em 3 anos. Perderia a capacidade de recalcular o passado e exigiria re-download em revisões.

### 7. TTL do cache bruto

**Decisão:** o cache bruto continua cumulativo; o TTL controla apenas a revalidação.

- Vendas/recompras: 1 h quando o cache contém o dia corrente ou o último dia útil; 6 h caso contrário.
- Estoque/cupom/vencimentos: 24 h.
- `304` reutiliza o CSV e atualiza apenas `checked_at`.
- O TTL é aplicado por recurso, com metadados independentes.

**Racional:** o dado histórico é imutável para fins de análise; só o recurso corrente precisa de revalidação frequente. O estoque é mensal, então 1 h seria desperdício.

### 8. Health check da fonte de estoque

**Decisão:** antes de usar o estoque, validar:

- `package_show` com `success: true`;
- exatamente um recurso CSV de estoque;
- cabeçalho `Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque`;
- parsing mínimo de uma amostra;
- `latest_data_date` (mês) não mais de 3 meses atrás.

Falha de dataset/recurso/schema: `TesouroDataError`, sem fallback. Defasagem > 3 meses: aviso, mas o dado é usado como último disponível.

**Racional:** o spike não encontrou migração da fonte; o CKAN continua sendo a fonte oficial. O health check protege contra mudanças silenciosas.

### 9. Erros e logging

- `CommunicationError` para rede/HTTP/timeout/corpo parcial.
- `TesouroDataError` para schema, taxonomia, total zero, fonte ausente e health check.
- Falhas esperadas em uma linha; exceções inesperadas com traceback.
- Nenhum erro de análise deve apagar o cache bruto válido.

### 10. Dependências e ajustes nas changes pré-requisitas

Esta change depende de:

- `add-tesouro-direto-vendas` implementada;
- `add-tesouro-direto-resgates-estoque` implementada.

As changes pré-requisitas já foram ajustadas no planejamento para:

- remover a GUI (botão/janela/abas) — a GUI passa para `add-tesouro-gui`;
- alinhar o TTL do cache bruto com a decisão 7;
- manter o cache bruto cumulativo sem housekeeping.

## Risks / Trade-offs

- **[Título novo fora do registry]** → `OUTROS` + aviso + teste de título desconhecido; revisão do registry quando o portal publicar um título novo.
- **[Estoque mensal e defasado]** → rótulo “último mês consolidado”, health check com aviso > 3 meses e séries sempre mensais.
- **[Valor vs quantidade]** → headline por valor; quantidade como métrica secundária e rótulo explícito.
- **[Revisões do CSV]** → invalidação por hash e recálculo completo das partições; 3 anos de dados são baratos de recalcular.
- **[Fonte migrar ou sumir]** → health check falha com `TesouroDataError`; sem fallback silencioso.
- **[Concorrência CLI/GUI]** → `ActionLock` dedicado para analytics; escrita atômica e manifest por último.
- **[Precisão]** → `Decimal` no cálculo; quantização apenas na formatação; sem float no núcleo.
- **[Câmbio futuro]** → contrato `SeriesProvider` genérico; nenhuma dependência de modelos do Tesouro no renderizador.
- **[Cache bruto grande]** → ~15 MB; aceitável para um desktop; não podar evita re-download e perda de revisões.

## Migration Plan

1. Implementar após as duas changes pré-requisitas e após os ajustes de GUI/TTL nelas.
2. Na primeira execução, o analytics é construído a partir do raw; não há migração de dados.
3. Se o schema do raw mudar, o analytics é invalidado e recalculado.
4. Rollback: remover `analytics/` e o `manifest.json`; o raw permanece intacto.
5. A GUI só consumirá esta camada em `add-tesouro-gui`; até lá, a API headless é validada por testes.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
