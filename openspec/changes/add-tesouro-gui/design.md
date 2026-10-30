## Context

A GUI atual é uma única janela Tkinter construída diretamente no `root` por `SelicPreApp` e seus mixins (`WindowMixin`, `StatusMixin`, `ActionsMixin`, `ChartMixin`, `SidebarMixin`, `FetchMixin`). O layout tem barra superior, opções de visualização, `PanedWindow` com gráfico + análise, toolbar e statusbar.

As changes de Tesouro Direto planejam uma janela `Toplevel` separada com abas de tabelas. Esta change substitui esse desenho por uma janela única com abas de nível superior e sub-abas analíticas, com carregamento lazy.

O orçamento de testes de UI está em 5/5. A camada analítica (`add-tesouro-analise-percentuais`) fornece séries headless; esta change é só apresentação.

## Goals / Non-Goals

**Goals:**

- Shell de abas `SELIC Pré`, `Tesouro Direto` e extensão futura `Câmbio`.
- Preservar a tela SELIC Pré atual, sem alteração de comportamento.
- Sub-abas `Visão geral`, `Estoque` e `Apetite do mercado`, cada uma com percentual atual e evolução.
- Lazy rendering por visibilidade, com cache-only na primeira exibição.
- Atualização, progresso e status independentes por sub-aba.
- Manter os 5 testes de UI e testar o restante headless.

**Non-Goals:**

- Conteúdo de Câmbio, dólar ou ouro.
- Tabelas brutas de vendas/resgates no GUI.
- Projeções futuras.
- Alterar o gráfico principal, a análise lateral ou a busca SELIC Pré.
- Exportação dedicada, MCP ou banco de dados.
- Novos cálculos analíticos; esta change consome `tesouro-analise`.

## Decisions

### 1. Shell + controllers de aba

**Decisão:** separar o shell da tela atual.

```text
AppShell
+-- MainNotebook
    +-- SelicPreTab          (conteudo atual, inalterado)
    +-- TesouroDiretoTab
        +-- SubNotebook
            +-- VisaoGeralTab
            +-- EstoqueTab
            +-- ApetiteTab
    +-- (CambioTab futuro)
```

- `AppShell` mantém `root`, `tk`, `ttk`, `deps`, `settings`, geometria, título, escudo e registro de abas.
- `SelicPreTab` recebe o frame da aba e reutiliza os mixins atuais; `self.root` continua sendo o root para `after`, clipboard e geometria; os widgets são parented no frame da aba.
- `TesouroDiretoTab` é um controller que cria o sub-notebook e delega para os controllers.
- `GuiDependencies` ganha as fábricas/adaptr de análise do Tesouro; `launch.py` compõe o shell.

**Alternativa rejeitada:** manter tudo em `SelicPreApp` e adicionar condicionais de aba. A classe já concentra muitos mixins; o shell separado evita acoplamento e permite Câmbio sem reestruturação.

### 2. Registro de abas e lazy controller

**Decisão:** introduzir um registro headless:

```text
TabSpec(id, label, factory)
LazyTabRegistry(specs)
  ensure_built(tab_id)
  mark_visible(tab_id)
  is_built(tab_id)
  ordered_specs()
```

- O registry não importa Tkinter; é testável com fakes.
- O adaptador Tk escuta `<<NotebookTabChanged>>` e chama `ensure_built` para a aba visível.
- `ensure_built` é idempotente; a primeira chamada cria os widgets, a segunda só atualiza.
- O startup constrói apenas `SELIC Pré`; `Tesouro Direto` é construída na primeira seleção.
- Dentro de `Tesouro Direto`, `Visão geral` é construída na primeira exibição; `Estoque` e `Apetite` quando selecionadas.
- Um flag `_shell_ready` evita que eventos de `<<NotebookTabChanged>>` disparem durante a montagem.

**Alternativa rejeitada:** construir tudo no startup e apenas ocultar. Aumentaria o tempo de abertura e criaria canvases matplotlib desnecessários.

### 3. Reparentamento da tela SELIC Pré

**Decisão:** os métodos de construção atuais passam a receber o frame da aba em vez do `root`.

- A barra superior, as opções de visualização, o `PanedWindow`, a toolbar e a statusbar ficam dentro de `SelicPreTab`.
- `root` continua sendo usado para `bind`, `after`, `clipboard`, `geometry`, `state` e `iconphoto`.
- Nenhuma lógica de busca, gráfico ou análise é reescrita.
- Os 5 testes de UI existentes são adaptados para acessar `app.selic_pre_tab` (ou equivalente) e continuam cobrindo o comportamento atual.

**Racional:** isolar a tela atual reduz o risco de regressão; a mudança é de parent, não de comportamento.

### 4. Atalhos e bloqueio por aba

**Decisão:** os atalhos globais passam por um guard de aba ativa.

- `F5`, `Ctrl-D`, `Ctrl-Shift-C`, `Ctrl-E`, `Ctrl-L` só executam quando `SELIC Pré` está ativa.
- O bloqueio de controles (`_set_ui_locked`) afeta apenas os widgets de `SelicPreTab`.
- As sub-abas do Tesouro têm seus próprios botões de atualização e estados de progresso.
- A statusbar é por aba; não há statusbar global compartilhada.

**Alternativa rejeitada:** statusbar global. Mensagens de contextos diferentes se misturariam e o usuário perderia a origem.

### 5. Layout e gráficos

**Decisão:** cada sub-aba tem dois gráficos matplotlib independentes.

- `Visão geral`:
  - Atual: barras agrupadas de estoque vs apetite por família.
  - Evolução: linha do gap (apetite − estoque) por família.
- `Estoque`:
  - Atual: barra 100% empilhada por família, com segmentos por título.
  - Evolução: área 100% empilhada por família, mensal.
- `Apetite do mercado`:
  - Atual: barra 100% empilhada por família, com segmentos por título, agregada na janela.
  - Evolução: área 100% empilhada por família, com buckets diário/semanal/mensal.
- O eixo Y dos gráficos de percentual fica em 0–100%; o gap fica em torno de zero.
- O título de cada gráfico indica a janela e a data-base (ex.: “14 dias até 28/10/2026”).
- A renderização fica em `presentation/charts_tesouro.py`; os dados vêm de `SeriesPoint` da aplicação.

**Racional:** dois gráficos separados atendem ao pedido e evitam eixos duplos confusos. A barra atual mostra família e título; a evolução mostra a tendência.

### 6. Filtros e janelas

**Decisão:** cada sub-aba tem um seletor de janela `14d`, `3m`, `12m`, `3a`.

- `Estoque`: sempre mensal; `14d` mostra o último mês consolidado; `3m` mostra até 3 meses; `12m`/`3a` mostram 12/36 meses.
- `Apetite`: o percentual atual é a agregação da janela; a evolução usa buckets diário (14d), semanal (3m) e mensal (12m/3a).
- `Visão geral`: estoque no último mês; apetite na janela selecionada; gap alinhado por mês.
- As janelas são ancoradas no `latest_data_date`; nenhum período futuro é gerado.
- O rótulo da janela aparece no título do gráfico e no status.

**Alternativa rejeitada:** usar “hoje” como âncora. A defasagem do Tesouro produziria janelas vazias.

### 7. Carregamento, cache e threading

**Decisão:** primeiro show lê somente cache; atualização é explícita.

- `on_show()` chama o view-model para carregar o cache analítico e desenhar.
- Sem cache: renderiza estado vazio com “clique em Atualizar”; nenhuma rede.
- “Atualizar” usa o cache válido; “Ignorar cache” faz verificação condicional.
- O refresh roda em thread; o resultado volta via `root.after`.
- Cada sub-aba tem seu próprio `ActionLock`/controller de carga; falha isolada.
- Fechar a janela durante a carga cancela a atualização e ignora callbacks tardios.
- O progresso é indeterminado (não há `Content-Length`).

**Racional:** consistente com o padrão atual da GUI e com as specs de cache; evita download automático ao trocar de aba.

### 8. View-models headless

**Decisão:** cada sub-aba tem um view-model em `presentation/tesouro_analise_view_model.py` (ou módulo equivalente), sem Tkinter.

O view-model calcula:

- janela selecionada e rótulo;
- séries atual e de evolução;
- estado de carregamento, cache e erro;
- textos de status;
- habilitação de controles;
- dados para os dois gráficos.

Testes de janela, filtros, status e habilitação são headless. Os 5 testes de UI existentes cobrem apenas montagem/wiring do shell e da aba padrão.

### 9. Extensão futura de Câmbio

**Decisão:** o shell expõe um `TabRegistry` e não conhece Câmbio.

A change futura registra `CambioTab` com suas próprias sub-abas (Dólar/Ouro) e reutiliza o mesmo `LazyTabController`. Nenhuma alteração no shell é necessária.

**Alternativa rejeitada:** criar uma aba “Câmbio” vazia agora. Polui a UI e antecipa um contrato que ainda não existe.

### 10. Remoção da GUI das changes pré-requisitas

**Decisão:** a janela `Toplevel` e as abas de tabelas saem de `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque`.

- Dados brutos e tabelas ficam apenas na CLI.
- A GUI de Tesouro nasce nesta change, já no formato final.
- As specs `tesouro-direto-gui` e `tesouro-resgates-estoque-gui` das changes antigas são substituídas por `app-tabs` e `tesouro-analise-gui`.

## Risks / Trade-offs

- **[Refactor de GUI em código funcional]** → isolar a tela atual em um controller e só trocar o parent; adaptar os 5 testes existentes sem reescrever a lógica.
- **[Orçamento de UI cheio]** → lazy registry e view-models headless; nenhum teste de UI novo; reduzir o orçamento só se algum teste atual migrar.
- **[Eventos de aba durante a montagem]** → flag `_shell_ready` e `ensure_built` idempotente.
- **[Escudo de inicialização]** → criar o notebook antes do escudo e levantar o escudo após cada construção da aba padrão.
- **[Atalhos globais]** → guard de aba ativa; teste headless do guard.
- **[Canvases matplotlib]** → criar por sub-aba, apenas quando visível; destruir ao fechar.
- **[Fechar durante carga]** → flag de cancelamento e checagem de `winfo_exists` antes de atualizar.
- **[Status confuso]** → status por sub-aba, com fonte, extração e data-base.
- **[Usuário esperar tabelas brutas]** → deixar claro na UI que os dados brutos estão na CLI; não criar tabela escondida.
- **[Semântica de valor]** → rótulos “valor na metodologia do Tesouro” e “percentual por valor”; quantidade não é headline.

## Migration Plan

1. Implementar `add-tesouro-analise-percentuais` e ajustar as duas changes de dados (remover GUI, alinhar TTL).
2. Refatorar o shell e reparentar a tela SELIC Pré; rodar os 5 testes de UI adaptados.
3. Adicionar a aba Tesouro Direto com sub-abas lazy e view-models headless.
4. Adicionar os renderizadores e o wiring de dependências.
5. Validar `make lint`, `make complexity` e a suíte completa.
6. Rollback: manter a tela SELIC Pré como estava e desabilitar o registro da aba Tesouro; nenhum dado é migrado.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
