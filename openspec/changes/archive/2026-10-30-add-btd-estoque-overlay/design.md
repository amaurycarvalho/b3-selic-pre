# Design

## Context

Ver `proposal.md` para a motivação. Spike de 2026-10-30:

- CKAN `estoque-do-tesouro-direto`: maior mês `2026-08`, 9.134 linhas, `first_data_date=2002-01`, metadados atualizados em 2026-10-16.
- BTD setembro/2026: publicado em 2026-10-29. Página `https://www.tesourotransparente.gov.br/publicacoes/balanco-do-tesouro-direto-btd/2026/9`; anexo `Anexos_Balanço_TD - Set 2026.xlsx` em `https://thot-arquivos.tesouro.gov.br/publicacao-anexo/29563`.
- O XLSX tem 9 abas estáveis (`Índice`, `1.1`…`1.5`, `2.1`, `2.2`, `3.1`). A aba `2.1` é `ANEXO 2.1 - ESTOQUE POR TÍTULO`, com cabeçalho mensal de `Jan/04` a `Set/26`, valores em R$ milhões na primeira seção e percentuais na segunda.
- Comparação com o CKAN: meses de 2023–2025 batem dentro de centavos; em 2026 há uma diferença de R$ 969.288.953,99 em `Tesouro IPCA+` entre março e maio, compatível com reclassificação/revisão da fonte. Por isso o BTD nunca deve sobrescrever meses já existentes no CKAN.
- O BTD publica por volta do dia 25 do mês seguinte; o CKAN permaneceu um mês atrás mesmo após atualizar metadados.
- A API `thot-arquivos.tesouro.gov.br` expõe apenas download por ID (`/publicacao-anexo/{id}`); não há endpoint de listagem. A descoberta exige ler a página de publicação.

O estoque do BTD é menos granular que o CKAN (sem vencimento, PU e quantidade) e começa em 2004, contra 2002 do CKAN. A sub-aba `Estoque` consome apenas título, mês e valor, então o BTD é completo para ela, mas não para o dataset canônico/CLI.

## Goals / Non-Goals

**Goals:**

- Exibir na sub-aba `Estoque` o mês mais recente disponível, usando o BTD quando ele estiver à frente do CKAN.
- Manter o CKAN como fonte canônica, detalhada e histórica.
- Funcionar offline na primeira exibição, com cache próprio e sem rede.
- Não deixar a falha do BTD afetar o refresh do CKAN.
- Invalidar apenas a série `estoque` quando a sobreposição mudar.

**Non-Goals:**

- Substituir o CKAN, alterar o CSV bruto ou a CLI `tesouro-estoque`.
- Obter vencimento, PU ou quantidade do BTD.
- Criar progresso determinado para o download do BTD.
- Fazer scraping de qualquer página além da publicação BTD necessária para achar o XLSX.
- Aumentar o orçamento de testes de UI.

## Decisions

### 1. BTD como sobreposição, não como fonte primária

O merge adiciona apenas meses do BTD posteriores ao maior mês existente no CKAN e nunca substitui valores existentes. Os títulos do BTD são agregados por indexador e não têm correspondência um-a-um com os vencimentos do CKAN; portanto, meses sobrepostos são ignorados mesmo quando os nomes dos títulos diferem. Isso evita dupla contagem e preserva a granularidade do CKAN.

Alternativa rejeitada: trocar o CKAN pelo BTD. Perderia vencimento/PU/quantidade, a CLI e o histórico desde 2002, e introduziria divergências conhecidas em 2026.

### 2. Descoberta pela página de publicação mais recente

A página base `.../publicacoes/balanco-do-tesouro-direto-btd` resolve para a edição mais recente. O adaptador lê apenas o mês de referência, a data de publicação e o link do anexo XLSX. O parsing tolera variações de acentuação/rótulo do anexo e exige extensão `.xlsx` e `Content-Type` de planilha.

Alternativa rejeitada: inferir IDs numéricos do `thot-arquivos`; não são documentados nem estáveis. Alternativa rejeitada: usar o RMD; ele tem estoque da DPF, mas não o estoque do Tesouro Direto por título com o mesmo histórico.

### 3. Parsing XLSX com biblioteca padrão

Abrir o XLSX com `zipfile`, ler `xl/workbook.xml`, `xl/sharedStrings.xml` e a worksheet cujo `A1` começa com `ANEXO 2.1 - ESTOQUE POR TÍTULO`. O cabeçalho mensal é reconhecido por `MMM/AA`; a leitura para na primeira seção (R$ milhões) antes do bloco de percentuais e ignora linhas de total/agregado como `Estoque`. Valores são multiplicados por 1.000.000 e convertidos para `Decimal`.

Alternativa rejeitada: adicionar `openpyxl`/`pandas`. O projeto evita dependências novas e a planilha relevante é simples o bastante para leitura estrutural.

### 4. Modelo agregado separado

Criar `EstoqueMensalTitulo` em `domain` com `tipo_titulo`, `mes` e `valor_estoque`. O merge devolve uma sequência de registros que pode conter `EstoqueTesouroDireto` e `EstoqueMensalTitulo`; o pré-cálculo e o provider passam a aceitar um protocolo estrutural com esses três atributos. O modelo detalhado e todos os fluxos de CLI/parsing do CKAN ficam intocados.

Alternativa rejeitada: preencher `EstoqueTesouroDireto` com vencimento/PU/quantidade fictícios; violaria o contrato do domínio. Alternativa rejeitada: tornar os campos opcionais; ampliaria o impacto para parsing, formatação e CLI sem necessidade.

### 5. Cache normalizado próprio e opcional no hash analítico

O BTD normalizado é gravado atomicamente em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/estoque-btd.json`, com metadados ao lado (mês, publicação, URLs, `sha256` do XLSX, `checked_at`). TTL de 24 horas. A leitura inicial usa somente esse arquivo, sem rede.

A partição analítica `estoque` passa a depender de `estoque.csv` e, opcionalmente, de `estoque-btd.json`. `source_hashes`/`RAW_FILES` ganham suporte a dependência opcional com sentinela estável para ausência (`<absent>`), de modo que usuários sem BTD não invalidem a série e o aparecimento/remoção do arquivo invalide apenas `estoque`.

Alternativa rejeitada: tornar o arquivo BTD obrigatório; quebraria a leitura de cache existente até o primeiro refresh. Alternativa rejeitada: ignorar o hash do BTD; a série ficaria velha após o BTD acrescentar um mês.

### 6. Fluxo de refresh fail-soft

Para `KIND_ESTOQUE`, o loader busca primeiro o CKAN, depois tenta atualizar o BTD. O resultado do BTD é mergeado antes de montar `AnaliseData`/pré-cálculo. Qualquer falha do BTD é registrada como aviso e não altera o sucesso do CKAN. O status informa a data-base final e, quando aplicável, que a sobreposição BTD contribuiu ou que falhou.

## Risks / Trade-offs

- [Mudança no layout da página ou da aba da planilha] → validar cabeçalhos e aba esperados; falhar sem gravar cache e manter o anterior.
- [Publicação atrasada ou retificada] → TTL de 24h revalida a edição mais recente; como o merge nunca sobrescreve o CKAN, retificações do BTD só afetam meses ausentes.
- [Divergência de valores BTD × CKAN] → não sobrescrever; a sobreposição cobre apenas lacunas recentes.
- [Cache analítico revalidado a cada refresh] → hash opcional com sentinela estável evita recomputação quando não há BTD.
- [Leitura de XLSX sem dependência dedicada] → limitar o parser à aba e às linhas necessárias, com testes de arquivo real/fixture e falha explícita para formato inesperado.
- [Parsing de HTML no portal] → restringir a página de publicação do BTD e nunca interpretar conteúdo além dos metadados e do link do anexo.
- [Sobreposição afetar também `Visão geral`] → efeito desejado e coerente, pois a série de estoque é compartilhada; `Apetite` não é alterada.
