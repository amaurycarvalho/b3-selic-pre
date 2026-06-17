## Context

O aplicativo atualmente busca taxas SELIC Pré de uma única data na B3 e exibe um gráfico de linha (raw: DU252 × taxa, consolidado: ano × envelope min/max). Não há suporte para visualizar a evolução temporal da curva.

O usuário quer comparar a curva da data-base com curvas de 7, 14, 21 e 28 dias atrás, usando:
- Curvas superpostas com gradiente de cor (mais claro = mais antigo)
- Flechas (quiver) nos anos-chave 0, 1, 2, 3, 5, 10, 15 e 20 mostrando a transição entre datas consecutivas
- Dados baseados na taxa média por ano (avg de min_rate e max_rate do consolidado)
- UI com radio buttons (3 modos mutualmente exclusivos)
- Indicador de progresso durante a busca multi-data

## Goals / Non-Goals

**Goals:**
- Função `average_rate_by_year(records)` → `dict[int, float]` (ano → taxa média)
- Função `fetch_rates_download(date_str)` usando endpoint `GetDownloadFile` (retorna base64 CSV)
- Função `fetch_historical_rates(base_date)` que busca 5 datas (base − 28, 21, 14, 7, 0 dias) com `concurrent.futures.ThreadPoolExecutor` (4 workers)
- Função `render_curve_evolution(fig, date_rates_dict)` que plota 5 curvas + flechas quiver
- Radio buttons na GUI: "Detalhado", "Consolidado", "Evolução da curva"
- DatePicker popup calendar para entrada de data
- Limite de 30 dias corridos para consultas nos modos Detalhado e Consolidado (data informada não pode ser anterior a 30 dias da data atual)
- Indicador de progresso na status bar durante fetch multi-data
- "Copiar dados" no modo evolução exporta CSV consolidado das 5 datas
- Testes para: average_rate_by_year, fetch_rates_download, fetch_historical_rates, render_curve_evolution

**Non-Goals:**
- Não altera o comportamento dos modos Detalhado e Consolidado existentes (exceto validação de 30 dias)
- Não adiciona animação ou slider temporal
- Não modifica a interface CLI
- Não adiciona dependências externas (quiver já está no matplotlib; DatePicker é implementado com tkinter puro)

## Decisions

### Decision 1: Cálculo da taxa média por ano

**Decisão**: `average_rate_by_year` computa `(min_rate + max_rate) / 2` para cada ano a partir do resultado de `consolidate_by_year`.

**Rationale**: Reutiliza `consolidate_by_year` existente em vez de duplicar lógica de agrupamento. A média do envelope é uma métrica simples e intuitiva para comparar curvas.

**Alternativa**: Calcular média de todas as taxas do ano (não só min/max). Rejeitada: o usuário explicitamente pediu a média entre maior e menor.

### Decision 2: Endpoint GetDownloadFile para dados históricos (vs GetList)

**Decisão**: Usar o endpoint `GetDownloadFile` da B3 (retorna CSV em base64) para buscar taxas de datas históricas. Usar `GetList` (retorna JSON paginado) apenas para a data atual.

**Rationale**: 
- `GetList` SEMPRE retorna a taxa mais recente independentemente do parâmetro `date` — não serve para dados históricos
- `GetDownloadFile` retorna dados específicos da data informada
- `GetDownloadFile` requer `{"language":"pt-br","date":"YYYY-MM-DD","id":"SLP"}` (sem pageNumber/pageSize)
- Resposta é uma única linha de base64 decodificada para CSV com colunas: `Descrição da Taxa;Dias Úteis;Dias Corridos;Preço/Taxa`
- `page_size=100` é o máximo que a B3 aceita no `GetList` (valores ≥150 retornam vazio)

**Risco**: `GetDownloadFile` tem janela de retenção de aproximadamente 30 dias úteis. **Mitigação**: fallback para `fetch_reference_rates(..., page_size=100)` quando `GetDownloadFile` retorna vazio.

### Decision 3: 4 curvas históricas (7, 14, 21, 28 dias) + data-base

**Decisão**: Usar `_days_ago(base_date, days)` com `EVOLUTION_DAYS = [28, 21, 14, 7, 0]` para gerar as 5 datas.

**Rationale**: 
- Dias corridos são mais intuitivos que semanas
- 28 dias ≈ 1 mês (janela máxima suportada pelo `GetDownloadFile`)
- 5 curvas é suficiente para análise de tendência sem poluição visual
- Ordem crescente para o progresso: do mais antigo (28) para o mais recente (0 = base)

**Alternativa**: Semanas (2, 4, 8, 16, 32, 64). Rejeitada: `GetDownloadFile` não cobre datas tão antigas; semanas são menos intuitivas.

### Decision 4: Flechas quiver nos anos-chave com offset horizontal

**Decisão**: Desenhar flechas quiver apenas nos anos 0, 1, 2, 3, 5, 10, 15, 20. Cada transição (t → t+1) em um ano-chave ganha uma flecha com leve offset horizontal para evitar sobreposição.

```python
X = ano_chave + t * 0.06
Y = taxa_média_t[ano_chave]
U = 0.06
V = taxa_média_{t+1}[ano_chave] - taxa_média_t[ano_chave]
ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=1,
          color=transition_colors[t], width=0.004)
```

**Rationale**: 
- 8 anos-chave × 4 transições = 32 flechas (vs 80 se todos os anos)
- Offset horizontal cria uma "corrente" visual em cada ano-chave
- Cores gradiente ajudam a distinguir transições recentes vs antigas

**Alternativa**: Flechas em todos os anos. Rejeitado por poluição visual.

### Decision 5: Gradiente de cor nas curvas (5 curvas)

**Decisão**: Usar gradiente `Blues` do matplotlib onde a curva mais antiga (28d) recebe alpha=0.3 e a data-base alpha=1.0, com espessura de linha crescente (0.5 → 2.0).

```python
colors = plt.cm.Blues(np.linspace(0.3, 0.9, 5))
alphas = np.linspace(0.3, 1.0, 5)
linewidths = np.linspace(0.8, 2.5, 5)
```

**Rationale**: Gradiente comunica intuitivamente a ordenação temporal (claro=antigo, escuro=recente). Alpha decrescente em curvas antigas reduz poluição visual.

### Decision 6: Radio buttons substituindo checkbox

**Decisão**: Três `ttk.Radiobutton` em vez de um `ttk.Checkbutton`:

```
◉ Detalhado   ○ Consolidado   ○ Evolução da curva
```

**Rationale**: Os três modos são mutualmente exclusivos. Radio button é o widget correto para isso.

**Mapeamento de valores**:
- `"raw"`: gráfico detalhado (linha verde DU252 × taxa)
- `"consolidated"`: envelope min/max por ano
- `"evolution"`: 5 curvas com gradiente + flechas quiver

### Decision 7: Indicador de progresso no fetch multi-data

**Decisão**: Durante a busca, a status bar exibe "Buscando taxas históricas... (N/5 concluídas)" e é atualizada a cada data concluída. O botão "Buscar" fica desabilitado.

**Rationale**: O fetch multi-data leva mais tempo. Feedback explícito evita que o usuário pense que o programa travou.

### Decision 8: "Copiar dados" no modo evolução exporta CSV completo

**Decisão**: O CSV copiado contém todas as 5 datas no formato:

```
DATA;ANO;TAXA_MEDIA
2026-06-17;0;14.23
2026-06-17;1;14.45
...
2026-05-20;0;14.10
...
```

**Rationale**: Dados completos permitem análise offline. O formato CSV com data explícita é mais útil que apenas a média da data-base.

### Decision 9: Limite de 30 dias para consulta (raw/consolidated)

**Decisão**: Nos modos Detalhado e Consolidado, bloquear consultas para datas com mais de 30 dias corridos no passado. O modo Evolução não tem esse bloqueio (já busca automaticamente datas históricas).

**Rationale**: 
- O endpoint `GetDownloadFile` tem janela de retenção de ~30 dias úteis
- Datas muito antigas retornam resultados vazios ou inconsistentes
- O usuário recebe feedback imediato em vez de dados vazios/missing

**Mitigação**: Exibir mensagem clara na status bar: "Data muito antiga. Informe uma data nos últimos 30 dias."

### Decision 10: DatePicker popup calendar

**Decisão**: Implementar `DatePicker` com tkinter puro (sem dependências externas): janela popup com navegação mês/ano (`<` `>`) e grid de dias clicáveis. Ao selecionar um dia, a data é inserida no campo `date_var` no formato `YYYY-MM-DD`.

**Rationale**: 
- Entrada manual de data (`YYYY-MM-DD`) é propensa a erros de formato
- Calendário visual é mais intuitivo
- Evita dependência externa (`tkcalendar`)
- Botão `📅` ao lado do campo de data abre o popup

### Decision 11: Título do gráfico reposicionado (y=0.92)

**Decisão**: Em todos os três modos, o título do gráfico é posicionado em `y=0.92` (approximadamente duas alturas de fonte abaixo do topo) via `fig.suptitle(..., y=0.92)`.

**Rationale**: A toolbar do matplotlib (zoom/pan/home) sobrepõe o título na posição padrão (`y=0.98`). `y=0.92` empurra o título para baixo, mantendo-o visível.

## Risks / Trade-offs

- **[B3 GetDownloadFile retention window]** `GetDownloadFile` só cobre ~30 dias úteis. **Mitigação**: Fallback para `GetList` com `page_size=100` quando retorna vazio.
- **[B3 page_size=100 max]** `GetList` não aceita page_size ≥ 150. **Mitigação**: Usar `page_size=100` e iterar páginas (max 2 páginas para dados típicos).
- **[Rate limiting da B3]** 5 requisições paralelas podem ser rejeitadas. **Mitigação**: 4 workers no ThreadPoolExecutor; timeout de 15s por requisição.
- **[Poluição visual das flechas]** 32 flechas ainda podem ser excessivas. **Mitigação**: Alpha baixo (0.5) nas flechas de transições mais antigas; esconder flechas se zoom estiver muito afastado.
- **[Mudança de widget]** Usuários acostumados com o checkbox podem estranhar o radio button. **Mitigação**: Mesma posição na tela; label claro em cada opção.
- **[Re-fetch ao trocar modo]** Se o usuário trocar de "Detalhado" para "Evolução", os dados históricos ainda não existem. **Mitigação**: Botão "Buscar" separado; ao trocar para "Evolução", auto-preenche data atual e exibe "Clique em Buscar para carregar dados históricos".
- **[Flechas podem sobrepor curvas]** Se a variação entre datas for muito pequena, flechas viram pontos. **Mitigação**: Se `max(|V|) < 0.01`, não desenhar flechas e mostrar aviso na status bar.
- **[DatePicker em popup]** Pode não seguir o tema do sistema. **Mitigação**: Usar `tk.simpledialog.Dialog` como base; fundo branco consistente.
