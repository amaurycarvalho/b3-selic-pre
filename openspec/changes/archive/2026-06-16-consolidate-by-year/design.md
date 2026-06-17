## Context

A aplicação `b3_selic_pre.py` possui duas interfaces: CLI (argparse + CSV stdout) e GUI (tkinter Treeview). Ambas consomem a mesma lista de `RateRecord` objects vindos da B3. A visualização atual mostra um registro por linha (day252, day360, rate). Para períodos longos (ex.: 2520 registros para 10 anos), fica inviável analisar padrões visualmente.

A consolidação por ano agrupa registros usando `day360 // 365` como chave e reduz cada grupo a duas métricas: taxa mínima e taxa máxima. É uma transformação puramente derivativa — não requer novos dados externos.

## Goals / Non-Goals

**Goals:**
- Função pura `consolidate_by_year(records)` que transforma `list[RateRecord]` em `list[dict]` com `{year, min_rate, max_rate}`
- Flag CLI `--yearly` que altera o formato de saída de raw CSV para consolidado CSV
- Checkbox na GUI "Consolidar por ano" que alterna a view da tabela entre raw e consolidado
- "Copiar tabela" e "Exportar CSV" respeitam o modo de visualização ativo
- Testes para a função de consolidação, formato CLI e toggle GUI

**Non-Goals:**
- Não altera o schema de `RateRecord` (a consolidação é derivada, não armazenada)
- Não adiciona dependências externas
- Não modifica a API de fetch da B3
- Não suporta agrupamento por outros períodos (mensal, trimestral, etc.)

## Decisions

### 1. `consolidate_by_year` retorna lista de dicionários em vez de novos objetos
- **Decisão**: Retornar `list[dict]` simples em vez de criar um novo dataclass ou NamedTuple.
- **Rationale**: A estrutura de saída (year, min_rate, max_rate) é específica da view consolidada. Um dataclass adicionaria ruído sem benefício claro. Dicionários são flexíveis para formatação tanto em CSV quanto em Treeview.
- **Alternativa**: Criar `ConsolidatedYearRecord`. Rejeitada: acrescenta complexidade sem ganho de segurança de tipo significativo.

### 2. Chave de agrupamento é `day360 // 365`
- **Decisão**: Usar `day360 // 365` (divisão inteira).
- **Rationale**: `day360` representa dias corridos desde o início da série. A divisão inteira por 365 produz um ano zero-indexado (0, 1, 2...). Simples, determinístico, não requer parsing de data.
- **Alternativa**: Agrupar por ano calendário real. Rejeitada: a B3 não fornece data de cada registro, apenas day252 e day360.

### 3. CLI: flag `--yearly` ao invés de subcomando
- **Decisão**: Flag booleana simples no argparse existente.
- **Rationale**: Mínima intrusão no CLI atual. Quando presente, substitui `format_cli_rows` por `format_yearly_rows`.
- **Alternativa**: Subcomando `consolidate`. Rejeitado: excesso de complexidade para uma única opção.

### 4. GUI: checkbox substitui conteúdo da tabela
- **Decisão**: Um `ttk.Checkbutton` que, ao ser alternado, re-renderiza a tabela com os registros atuais no formato escolhido.
- **Rationale**: Evita manter duas tabelas ou abas. O usuário vê raw OU consolidado, nunca ambos simultaneamente — reduz ambiguidade sobre o que será copiado/exportado.
- **Alternativa**: Abas separadas (Notebook). Rejeitado: sobrecarga visual desnecessária para uma única alternância.

### 5. Export/Copy usa a view ativa
- **Decisão**: `copy_records` e `export_records` verificam o estado do checkbox e formatam de acordo.
- **Rationale**: Comportamento esperado: o que está na tela é o que sai. Sem surpresas.

### 6. Formato decimal brasileiro na saída consolidada
- **Decisão**: O consolidado (CLI e GUI) exibe taxas no formato brasileiro: vírgula como separador decimal e exatamente 2 casas decimais. Um helper `_brl(value)` centraliza a formatação (`f"{value:.2f}".replace(".", ",")`).
- **Rationale**: O público-alvo é brasileiro; vírgula decimal é o formato esperado. O CSV writer do Python faz quoting automático dos valores com vírgula (ex.: `0,"14,50","14,70"`), o que é compatível com editores de planilha configurados em locale pt-BR.
- **Alternativa**: Manter ponto decimal. Rejeitada: inconsistente com a expectativa do usuário brasileiro.

## Risks / Trade-offs

- **[Ano zero-indexado pode confundir]** → Usuários podem estranhar "Ano 0" para registros do primeiro ano. Mitigação: o cabeçalho da coluna é "ANO" e a documentação explica o cálculo. Alternativamente, pode-se exibir `day360 // 365 + 1` como "ano mais intuitivo" — mas isso seria inconsistente com o requisito do usuário ("inteiro de DC dividido por 365").
- **[Rate com vírgula decimal]** → `rate: str` pode vir como `"14,40"` (B3 retorna com vírgula). Mitigação: `float(r.rate.replace(",", "."))` normaliza antes da conversão, funcionando tanto com ponto quanto vírgula.
- **[Toggle ativo sem dados]** → Se o usuário marca "Consolidar por ano" antes de buscar dados, a tabela fica vazia. É um estado inócuo; o toggle só produz efeito quando há records. Pode-se desabilitar o toggle quando não há dados.
- **[CSV quoting em valores com vírgula]** → O consolidado CSV usa vírgula como separador decimal, o que faz o CSV writer adicionar aspas automáticas (ex.: `0,"14,50","14,70"`). Isso é válido e esperado em editores brasileiros, mas pode surpreender quem esperar um CSV simples sem aspas.
