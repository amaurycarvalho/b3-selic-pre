# Design

## Context

See `proposal.md` - Why. O cache analítico existente guarda partições genéricas com `source_sha256` e `latest_data_date`, mas nenhum módulo o consome. A GUI lê o cache bruto via `TesouroDiretoClient.read_cached_*`, parseia os CSVs e monta os gráficos por meio de `TesouroAnaliseController` -> `TesouroAnaliseViewModel` -> `SeriesBuilder` -> `SeriesReader` -> `TesouroSeriesProvider.fetch`.

Restrições relevantes:

- `application` não pode importar `presentation`, `infrastructure`, Tkinter ou matplotlib.
- `presentation` não pode importar `infrastructure`, exceto as raízes de composição `presentation/cli.py` e `presentation/gui/launch.py`.
- O cache bruto é cumulativo e não pode ser podado.
- O cache analítico tem lock dedicado e escrita atômica.
- O orçamento de testes de UI é 5; novos testes devem ser headless.

## Goals / Non-Goals

**Goals:**

- Evitar o parse dos CSVs brutos na primeira exibição e na troca de janela das três sub-abas.
- Recalcular apenas a fonte cujo conteúdo bruto mudou, com granularidade por fonte.
- Manter o pré-cálculo fora da thread da UI e reutilizar os registros já parseados pelo refresh.
- Reutilizar o cache analítico, o lock e a escrita atômica existentes.
- Manter fallback funcional quando as séries pré-calculadas ainda não existem.

**Non-Goals:**

- Alterar o cache bruto, o TTL, a CLI ou o servidor MCP.
- Pré-calcular dimensões que a GUI não usa (`produto+vencimento`).
- Substituir matplotlib ou mudar o desenho dos gráficos.
- Criar cache em memória por sessão além do cache em disco.

## Decisions

### 1. Pré-calcular séries normalizadas por fonte, não por sub-aba ou janela

**Decisão:** gerar três snapshots independentes:

```text
series/estoque   <- estoque.csv
series/demanda   <- vendas.csv
series/fluxo     <- vendas.csv + recompras.csv
```

Cada snapshot contém `SeriesPoint` para família e produto no menor bucket necessário: mensal para estoque e diário para demanda e fluxo, limitado aos 3 anos de retenção. Semanal e mensal são derivados na leitura, depois de filtrar o início exato da janela, para não incluir dias anteriores ao recorte. As janelas 14d/3m/12m/3a apenas filtram e agregam esses pontos.

**Racional:** as séries normalizadas são independentes de janela. Com isso, um único pré-cálculo serve todas as sub-abas e todas as janelas, sem a explosão combinatória de `(kind, window)`.

**Alternativas consideradas:**

- Payload final por `(sub-aba, janela)`: mais simples de ligar ao view-model, mas duplica cálculo e invalidação entre janelas.
- Cache dos registros parseados: evita o parse, mas ainda paga 0,2-5 s de montagem de gráfico e serializa listas grandes.

### 2. Invalidação por hash do CSV de origem

**Decisão:** cada snapshot guarda o `sha256` dos CSVs que o originaram. No refresh, comparar o hash atual com o registrado; só recalcular quando diferir. `checked_at` e `304` não invalidam.

- `series/estoque`: hash de `estoque.csv`.
- `series/demanda`: hash de `vendastesourodireto.csv`.
- `series/fluxo`: hash de `vendastesourodireto.csv` + `recompras.csv`.

**Racional:** `latest_data_date` pode não mudar em uma revisão histórica; o hash captura qualquer alteração de conteúdo e evita processamento desnecessário.

**Alternativa considerada:** usar apenas `latest_data_date` ou `etag`. É mais barato, mas não detecta revisões no histórico sem mudança de data.

### 3. Agregação em lote em uma passada

**Decisão:** adicionar uma função pura em `application/tesouro/` que percorre vendas, resgates e estoque uma vez e devolve os pontos por família/produto/bucket. O pré-cálculo usa essa função; não chama `TesouroSeriesProvider.fetch` por chave.

**Racional:** o `fetch` atual varre a lista inteira para cada chave (família/título), o que custa 4-5 s em 3 anos. Uma passada única mantém o custo do refresh próximo do parse já realizado.

**Alternativa considerada:** reutilizar `fetch` sem alterações. Menos código novo, mas o pré-cálculo ficaria caro o suficiente para anular o ganho percebido no botão `Atualizar`.

### 4. Persistência em snapshots fixos, não em partições por período

**Decisão:** gravar um arquivo por fonte (`series/estoque.json`, `series/demanda.json`, `series/fluxo.json`) com metadados e pontos. A escrita substitui o snapshot anterior de forma atômica; não há acúmulo de partições por período.

Cada snapshot inclui:

- `schema_version`;
- `source_sha256` dos CSVs de origem;
- `latest_data_date`, `extracted_at`, `source` e `titles`;
- pontos agrupados por dimensão e bucket.

**Racional:** o snapshot já é limitado a 3 anos na geração; não precisa de housekeeping por período. A substituição atômica simplifica leitura e invalidação. O manifest existente continua sendo gravado por último.

**Alternativa considerada:** partições mensais/diárias como no desenho original do cache analítico. Permite atualização incremental, mas exige compor dezenas de arquivos na leitura e não traz ganho para um snapshot de poucos MB.

### 5. Reaproveitar os dados já parseados pelo refresh

**Decisão:** o pré-cálculo recebe o `AnaliseData` retornado pelo loader da sub-aba, não relê os CSVs. Fontes não incluídas nesse `AnaliseData` não são recalculadas.

Mapeamento:

| Atualizar em | Fontes frescas | Snapshots recalculados |
| --- | --- | --- |
| `Estoque` | estoque | `estoque` |
| `Apetite do mercado` | vendas, resgates | `demanda`, `fluxo` |
| `Visão geral` | vendas, estoque | `demanda`, `estoque` |

**Racional:** evita reler e reparsear 14 MB logo após o refresh. Os snapshots não recalculados continuam válidos porque suas fontes não mudaram.

### 6. Leitura na apresentação via dependência injetada

**Decisão:** a leitura/gravação dos snapshots fica em `infrastructure/`, exposta como um adaptador injetado em `GuiDependencies` pela raiz de composição `gui/launch.py`. O loader de `presentation/tesouro_loaders.py` recebe esse adaptador e o cliente já injetado; não importa `infrastructure`.

O loader tenta montar um provider a partir dos snapshots. O `TesouroAnaliseController` passa a aceitar um provider já pronto em `AnaliseData`; se ausente, mantém o caminho atual de construção a partir dos registros brutos.

**Racional:** preserva as guardas de arquitetura e mantém o controller/view-model headless, sem Tkinter.

**Alternativa considerada:** mover a leitura para `application`. Seria possível, mas colocaria I/O de cache na camada de aplicação e contrariaria a separação atual entre cálculo puro e adaptadores.

### 7. Fallback único a partir do cache bruto

**Decisão:** na primeira exibição:

1. se os snapshots existem e os hashes conferem, usar as séries;
2. se faltam snapshots mas há cache bruto válido, montar as séries uma vez em background, persistir e desenhar, sem rede;
3. se não há nenhum dos dois, orientar `Atualizar`.

**Racional:** mantém a experiência atual para quem já tem cache bruto (inclusive gerado pela CLI) e fecha a lacuna da spec sem exigir um download.

**Alternativa considerada:** exigir sempre `Atualizar` quando o snapshot falta. É mais simples, mas piora a experiência de quem já possui dados brutos válidos.

### 8. Concorrência, falhas e esquema

- Escritas usam `analytics_lock` e `write_atomic`; o manifest é gravado por último.
- Dentro do lock, os hashes são reconferidos para evitar trabalho duplicado entre sub-abas.
- Leitura não adquire lock e nunca apaga, renomeia ou altera arquivos.
- Falha de pré-cálculo não desfaz o refresh; o snapshot anterior permanece.
- `schema_version` do cache analítico é incrementado; snapshots antigos são tratados como miss.
- Números `Decimal` são serializados como strings para não perder precisão na ida e volta.

## Risks / Trade-offs

- **[Pré-cálculo ainda caro em 3 anos]** -> agregação em uma passada, limitada a família/produto e aos buckets usados; medir antes de fechar a implementação.
- **[Snapshot grande]** -> poucos MB por fonte; descartar dimensões não usadas e limitar a 3 anos.
- **[Manifest global com `latest_data_date` de fontes diferentes]** -> usar o hash por snapshot como critério principal; não usar o campo global para invalidar séries.
- **[Corrida entre escrita da partição e do manifest]** -> escrita atômica e manifest por último; leitor pode ver conteúdo novo com manifesto antigo, mas nunca conteúdo parcial; a próxima leitura reconcilia pelo hash.
- **[Cache analítico ausente após upgrade]** -> fallback único a partir do cache bruto, seguido de persistência.
- **[Regressão no orçamento de UI]** -> novos testes de pré-cálculo, loader e controller são headless; o teste de UI existente não aumenta.

## Migration Plan

1. Subir `schema_version` do cache analítico; snapshots no formato antigo são ignorados.
2. Na primeira exibição após o upgrade, se houver cache bruto, as séries são montadas e gravadas em background.
3. No próximo `Atualizar`, só as fontes alteradas são recalculadas.
4. Rollback: remover `analytics/series/` e a entrada correspondente no manifest; o cache bruto permanece intacto e a GUI volta ao caminho antigo.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
