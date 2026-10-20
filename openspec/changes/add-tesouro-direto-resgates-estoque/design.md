## Context

A change `add-tesouro-direto-vendas` cria a base para consultar vendas do Tesouro Direto: cliente CKAN, cache, parsing, CLI `tesouro`, janela GUI, view-model headless e contratos de erro. Esta change estende essa base para os datasets de **resgates** e **estoque**, que o portal publica separadamente.

O spike complementar confirmou:

- resgates: `resgates-do-tesouro-direto` (`f30db6e4-6123-416c-b094-be8dfc823601`), com quatro recursos CSV, sendo um cupom duplicado;
- estoque: `estoque-do-tesouro-direto` (`4d4dac3b-96d2-4011-92c9-ddf7d8392622`), com um CSV mensal;
- todos os arquivos usam ASCII/UTF-8, `;`, decimal com vírgula, datas `DD/MM/YYYY` e quebra LF;
- recompras não tem `PU`; cupom e vencimentos tem;
- estoque usa `Mes Estoque` (`MM/YYYY`) e `Valor Estoque`;
- o cupom mais novo é um superconjunto do antigo;
- não há duplicatas nos datasets de resgates/estoque (diferente de vendas).

Esta change deve ser aplicada depois de `add-tesouro-direto-vendas`.

## Goals / Non-Goals

**Goals:**

- Consultar resgates (recompras, cupom e vencimentos) na CLI e na GUI.
- Consultar o estoque mensal na CLI e na GUI.
- Generalizar a descoberta e o cache para múltiplos recursos.
- Adicionar modelos `ResgateTesouroDireto` e `EstoqueTesouroDireto`.
- Reutilizar `CommunicationError`, `TesouroDataError`, `ActionLock`, XDG, retry e formatação.
- Manter testes headless e não aumentar o orçamento de UI.

**Non-Goals:**

- Vendas (change separada).
- Investidores, operações e taxas dos títulos.
- Tools MCP.
- Exportação no subcomando `exportar`.
- Gráficos.
- Banco de dados.
- Agendamento/cron.
- Cruzamento com a curva SELIC.

## Decisions

### 1. Registro de recursos e descoberta

**Decisão:** representar cada recurso lógico em um registro explícito, com pacote, nome do recurso, arquivo de cache, schema e modelo.

| Grupo | Recurso lógico | Nome no CKAN | UUID confirmado | Tamanho | Colunas |
| --- | --- | --- | --- | ---: | --- |
| resgates | `recompra` | Recompras do Tesouro Direto | `30c2b3f5-6edd-499a-8514-062bfda0f61a` | 6.419.565 | 5, sem `PU` |
| resgates | `cupom` | Pagamento de Cupom de Juros do Tesouro Direto | `b04812f4-c453-4298-a12e-0ad190998243` (mais novo) | 38.858 | 6, com `PU` |
| resgates | `vencimento` | Vencimentos do Tesouro Direto | `9180ec46-5d73-49ab-bd26-f16e2b323f74` | 7.919 | 6, com `PU` |
| estoque | `estoque` | Estoque do Tesouro Direto | `650cdc18-0513-4bb1-9222-003ad1c11ac7` | 718.044 | 6, com `Mes Estoque` e `Valor Estoque` |

Descoberta:

- `package_show` para `resgates-do-tesouro-direto` e `estoque-do-tesouro-direto`;
- validar `success: true`;
- filtrar recursos `format == "CSV"`;
- selecionar por nome/filename;
- para o cupom duplicado, escolher o recurso com maior `last_modified` (o mais novo é superconjunto do antigo);
- se houver mais de um candidato após a seleção, levantar `TesouroDataError`;
- se faltar um recurso, levantar `TesouroDataError`.

Os UUIDs confirmados servem para validação e testes; a seleção em runtime é por nome + `last_modified`, para tolerar recriação de recursos no CKAN.

### 2. Download e cache por recurso

**Decisão:** baixar e cachear cada recurso independentemente.

- Arquivos: `recompras.csv`, `cupom.csv`, `vencimentos.csv`, `estoque.csv`.
- Metadados: um arquivo por recurso (`recompras.metadata.json`, etc.) para permitir TTL e escrita atômica independentes.
- TTL de 6 horas por recurso, baseado em `checked_at`.
- `ETag`/`If-None-Match`, `Last-Modified`/`If-Modified-Since`; `304` atualiza apenas `checked_at`.
- Escrita atômica em bytes.
- Falha em um recurso preserva a versão anterior daquele recurso e não impede os demais.
- Leitura somente leitura para consumidores que não devem alterar o cache.
- Sem housekeeping.

**Racional:** os recursos têm tamanhos, periodicidades e frequências de mudança diferentes; um cache único dificultaria a invalidação e a atualização parcial.

### 3. Modelos

**Decisão:** dois frozen dataclasses.

`ResgateTesouroDireto`:

| Campo | Tipo | Observação |
| --- | --- | --- |
| `tipo_resgate` | `str` | `recompra`, `cupom` ou `vencimento` |
| `tipo_titulo` | `str` | valor da coluna `Tipo Titulo` |
| `vencimento` | `str` ISO | data de vencimento |
| `data_resgate` | `str` ISO | data do resgate |
| `pu` | `Decimal \| None` | `None` para recompras |
| `quantidade` | `Decimal` | quantidade |
| `valor` | `Decimal` | volume financeiro |

`EstoqueTesouroDireto`:

| Campo | Tipo | Observação |
| --- | --- | --- |
| `tipo_titulo` | `str` | valor da coluna `Tipo Titulo` |
| `vencimento` | `str` ISO | data de vencimento |
| `mes` | `str` | `AAAA-MM` |
| `pu` | `Decimal` | preço unitário |
| `quantidade` | `Decimal` | quantidade em estoque |
| `valor_estoque` | `Decimal` | valor do estoque |

**Racional:** separar os modelos evita campos opcionais sem sentido e reflete a semântica distinta de fluxo (resgates) e snapshot (estoque).

### 4. Parsing por recurso

**Decisão:** validar o cabeçalho exato de cada recurso, com normalização de caixa/acentos.

- Resgates/recompras:

```text
Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor
```

- Resgates/cupom e vencimentos:

```text
Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor
```

- Estoque:

```text
Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque
```

Conversões:

- `Data Resgate` `DD/MM/YYYY` → ISO;
- `Mes Estoque` `MM/YYYY` → `AAAA-MM`;
- decimais com vírgula → `Decimal`;
- `tipo_resgate` é derivado do recurso lógico, não de uma coluna.

O parsing deve:

- tentar `utf-8-sig`, `utf-8` e `latin-1`;
- usar `;` e não `csv.Sniffer`;
- exigir as colunas do recurso;
- ignorar colunas extras com aviso;
- preservar todas as linhas (não deduplicar);
- rejeitar CSV vazio ou sem registros com `TesouroDataError`;
- reportar linha e coluna em erros.

### 5. Filtros, agregação e ordenação

**Resgates:**

- filtro por `tipo_resgate`, título (parcial, sem caixa/acentos) e `data_resgate` inclusivo;
- período padrão: 30 dias na CLI e 12 meses na GUI, relativos à maior `data_resgate` disponível;
- agregação por `tipo_resgate` + `tipo_titulo`: somar `quantidade` e `valor`;
- `PU` médio ponderado apenas quando todas as linhas do grupo têm `PU`; para recompras, `PU_MEDIO` fica vazio;
- ordenação: `data_resgate` desc, `tipo_resgate`, `tipo_titulo`, `vencimento`, `pu`.

**Estoque:**

- filtro por título e `mes` inclusivo;
- padrão: **último mês disponível na CLI** e **12 meses na GUI**;
- a tabela pode mostrar vários meses, mas a agregação por título exige um único mês;
- NÃO somar `valor_estoque` entre meses; estoque é snapshot, não fluxo;
- agregação por título dentro do mês: somar `quantidade` e `valor_estoque`; `PU` médio ponderado;
- ordenação: `mes` desc, `tipo_titulo`, `vencimento`, `pu`.

**Racional:** recompras não tem `PU`; somar `PU` ou somar estoque entre meses produziria números sem significado.

### 6. CLI

**Decisão:** dois subcomandos de nível raiz, para não alterar a interface de vendas.

```text
b3-selic-pre tesouro-resgates [--tipo recompra|cupom|vencimento]
                              [--titulo T] [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD]
                              [--agregar] [--json] [--no-cache]

b3-selic-pre tesouro-estoque [--titulo T] [--inicio AAAA-MM] [--fim AAAA-MM]
                             [--mes AAAA-MM] [--agregar] [--json] [--no-cache]
```

- `tesouro-resgates`: padrão de 30 dias até a maior `data_resgate`.
- `tesouro-estoque`: padrão do último mês disponível; `--inicio`/`--fim` em `AAAA-MM` para intervalos; `--mes` para um mês específico.
- `--agregar` em estoque usa o mês selecionado; se o intervalo cobrir mais de um mês, é erro de uso.
- `--json` segue o mesmo envelope de vendas, com `dataset` e o campo específico (`tipo_resgate` ou `mes`).
- CSV de resgates: `TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;PU;QUANTIDADE;VALOR`.
- CSV de resgates agregado: `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO`.
- CSV de estoque: `TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE`.
- CSV de estoque agregado: `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO`.
- Códigos `0`/`1`/`2`, como em vendas.
- `--no-cache` faz verificação condicional; `304` reutiliza o cache.

### 7. GUI

**Decisão:** adicionar abas à janela "Tesouro Direto" existente.

- `ttk.Notebook` com abas `Vendas`, `Resgates` e `Estoque`.
- `Vendas` permanece como definido na change de vendas.
- `Resgates`: filtro por tipo (`Todos`, `Recompra`, `Cupom`, `Vencimento`), título e período; 12 meses; limite de 5.000 linhas; atualização e status próprios.
- `Estoque`: filtro por título e intervalo de meses; 12 meses; tabela de snapshots; agregação por título para o mês selecionado; atualização e status próprios.
- Cada aba tem seu próprio cache, carregamento e mensagens; falha em uma aba não bloqueia as demais.
- O download/parsing roda em thread e a UI é atualizada via `root.after`.
- Fechar a janela durante a carga não pode gerar exceção.
- O view-model de cada aba é headless.
- Sem aumento do orçamento de UI.

### 8. Erros e logging

- `CommunicationError` para rede/HTTP/timeout/corpo vazio/parcial/Content-Type inválido.
- `TesouroDataError` para CSV/schema/valores inválidos e recurso ausente ou ambíguo.
- Falha em um recurso é reportada no recurso/aba correspondente; os demais continuam disponíveis.
- Falhas esperadas em linha única; exceções inesperadas com traceback.
- CLI em `stderr`; GUI no status da aba.

### 9. Testes e governança

- Testes headless para descoberta, seleção do cupom mais novo, parsing por recurso, cache por recurso, filtros, agregação e formatação.
- Testes de UI apenas para montagem/wiring, sem aumentar o orçamento de 5.
- `make lint`, `make complexity` e suíte completa.
- Manter as guardas de arquitetura.

## Risks / Trade-offs

- **[Cupom duplicado]** → escolher o recurso com maior `last_modified`; teste específico.
- **[Recompras sem `PU`]** → `PU` opcional e `PU_MEDIO` vazio na agregação.
- **[Estoque é snapshot]** → não somar entre meses; agregação exige um mês.
- **[Múltiplos downloads]** → cache e status por recurso; falhas independentes.
- **[CSV adicional ~7,2 MB]** → download em chunks, timeout de 60 s e progresso indeterminado.
- **[Portal instável]** → retry transitório e preservação da versão anterior.
- **[Schema futuro diferente]** → validar cabeçalho e falhar como `TesouroDataError`.
- **[Volume de resgates]** → 102.502 linhas em recompras; filtros e limite de 5.000 na GUI.

## Dependencies

- `add-tesouro-direto-vendas` deve ser implementada/arquivada antes desta change.
- Reutiliza `tesouro_client`, `tesouro_cache`, `tesouro_cached_client`, `application/tesouro`, `presentation/tesouro_view_model.py` e a janela `presentation/gui/tesouro.py`.
