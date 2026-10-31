# Design

## Context

Ver `proposal.md` para a motivação. Hoje a aba Tesouro Direto constrói a sub-aba de forma síncrona no primeiro `<<NotebookTabChanged>>` e só depois inicia a leitura do cache em background. A leitura leva cerca de 0,5 s e cada gráfico leva de 0,3 s a 1,5 s para ser montado/desenhado na thread da UI. O aviso atual aparece como conteúdo dos gráficos ou como overlay sobre eles, o que pode deixar resíduos e deslocar o layout.

As sub-abas Dólar e Ouro e Reservas Internacionais carregam em background, mas não usam o ponteiro de espera. A aba Sobre usa um `Text` somente leitura; o resumo de funcionalidades ainda não existe no README nem na interface.

Os renderizadores chamam `tight_layout` diretamente em `charts.py`, `charts_tesouro.py`, `charts_market.py` e `charts_reserves.py`. Quando as margens não acomodam títulos, legendas e rótulos, o matplotlib emite `UserWarning` em vez de falhar, mas o aviso aparece para o usuário e não é registrado no log. Os pontos observados foram `charts_tesouro.py` (comparação e gap) e `charts_reserves.py` (renderização principal).

As sub-abas `Dólar e Ouro` e `Reservas Internacionais` usam carregamento em background e ponteiro de espera, mas ainda mostram o painel antigo durante a carga, não têm texto fixo de processamento e mantêm a barra de progresso diretamente na statusbar. A aba de nível superior também ainda se chama `Câmbio e Ouro`.

## Goals / Non-Goals

**Goals:**

- Mostrar um texto fixo atrás dos gráficos enquanto o conteúdo não está pronto.
- Ocultar os gráficos durante a seleção da sub-aba e durante `Atualizar`.
- Reexibir os gráficos somente depois que a carga de dados e o desenho terminarem.
- Manter ponteiro, statusbar e progresso indicando o processamento.
- Evitar deslocamentos de layout ao ocultar/reexibir gráficos ou ao mostrar a barra de progresso.
- Publicar um resumo único de funcionalidades no README e na aba Sobre.
- Impedir que avisos de layout do matplotlib vazem para o usuário e registrá-los no log com contexto.
- Aplicar às sub-abas de câmbio e reservas o mesmo feedback visual das sub-abas do Tesouro Direto.
- Renomear a aba de nível superior para `Câmbio e Reserva` no shell, README e aba Sobre.

**Non-Goals:**

- Otimizar o tempo de montagem/desenho ou mover matplotlib para outra thread.
- Alterar cache, TTL, clientes HTTP, payloads ou contratos de dados.
- Adicionar progresso determinado às sub-abas.
- Mudar o comportamento de `Atualizar` além de ocultar/reexibir os gráficos.

## Decisions

### 1. Texto fixo atrás dos gráficos

`TesouroSubTab` cria um `ttk.Label` centralizado com `Processando as informações. Aguarde…` dentro do frame dos gráficos. O label é posicionado com `place` e mantido abaixo dos painéis com `lower()`. Enquanto os painéis estão visíveis, eles cobrem o texto; quando são ocultados, o texto aparece.

Durante o processamento, `current_panel.frame` e `evolution_panel.frame` são removidos com `pack_forget`; ao final, são reempacotados e o label volta a ser abaixado. O texto é fixo, não flutua sobre o gráfico e não participa do cálculo de geometria.

Alternativa rejeitada: overlay flutuante sobre os gráficos. O overlay alterava a organização visual e deixava resíduos ao trocar de aba.

### 2. Ocultar na seleção e no Atualizar; reexibir após a carga

- Ao selecionar/re-exibir uma sub-aba, os gráficos são ocultados antes da leitura do cache e do desenho; o texto fixo aparece.
- Ao acionar `Atualizar`, os gráficos são ocultados antes do worker e permanecem ocultos durante a busca, o processamento e o desenho.
- Os gráficos só são reexibidos em `_finish_load`, depois de `update_loading_state(False)`, do desenho e de um `draw_idle()` adicional para o canvas já mapeado.
- Em falha, os gráficos também são restaurados, com a mensagem de erro na statusbar.
- Na troca de janela, os gráficos permanecem visíveis; apenas o ponteiro de espera é usado.

Alternativa rejeitada: manter os gráficos visíveis durante o processamento. O conteúdo parcial e o redesenho atrasado causavam a impressão de movimento estranho.

### 3. Indicador de ocupação compartilhado

Criar `presentation/busy.py` com `WaitCursor` e `BusyIndicator`:

- `WaitCursor` aplica `watch` recursivamente à árvore de widgets, guardando e restaurando o cursor original de cada widget. Isso cobre `tk.Text` (`xterm`) e canvas, que não herdam o cursor da raiz.
- `BusyIndicator` associa o cursor a um label opcional; `enter()`/`leave()` são simétricos e toleram janela destruída.

O aviso de construção da aba Tesouro usa o mesmo helper antes de criar a sub-aba, para que a janela pinte o texto antes do trabalho pesado. Depois da construção, esse aviso é escondido e a sub-aba usa o texto fixo atrás dos gráficos.

Alternativa rejeitada: `root.config(cursor="watch")` direto em cada sub-aba. Cargas concorrentes poderiam restaurar o ponteiro cedo demais.

### 4. Layout estável

O progresso indeterminado passa a viver em um host de largura fixa (140 px) sempre empacotado na statusbar; a barra é empacotada/desempacotada apenas dentro desse host. Os rótulos de status e de detalhe usam `width=1` com `fill=X, expand=True`, para que mudanças de texto não alterem a largura requisitada.

`update_loading_state(False)` é aplicado antes de `_draw`, e os painéis só são reexibidos depois do desenho. Ocultar/reexibir os painéis com `pack_forget`/`pack` mantém a largura do `PanedWindow`, a posição do sash e a largura do canvas estáveis.

Alternativa rejeitada: empacotar a barra diretamente na statusbar. O aparecimento/desaparecimento alterava a largura requisitada e deslocava o gráfico.

### 5. Resumo de funcionalidades com fonte única

Criar em `application/about.py` o título `Funcionalidades`, a lista `FEATURES_SUMMARY` e `features_text()`. A aba Sobre monta a seção com `features_text()`, mantendo `Aplicação:` antes de `Funcionalidades:`; o README recebe a mesma lista. Um teste headless extrai a seção do README, normaliza espaços e compara com `features_text()`.

Alternativa rejeitada: duplicar o texto sem teste. README e interface já divergem em outros pontos, e o resumo deve permanecer consistente.

### 6. Hardening do layout dos gráficos

Os pontos vulneráveis são todas as chamadas diretas a `tight_layout` nos renderizadores: `_render_empty`, `render_chart`, `render_curve_evolution` e `render_detailed_evolution` em `charts.py`; `_empty`, `render_current_share`, `render_current_comparison`, `render_evolution` e `render_gap` em `charts_tesouro.py`; `_empty` e `render_reserves` em `charts_reserves.py`; e `_empty` e `render_market` em `charts_market.py`.

Criar `presentation/chart_layout.py` com `apply_tight_layout(fig, *, context, pad=None)`. O helper executa o layout dentro de `warnings.catch_warnings(record=True)`:

- Avisos `Tight layout not applied` são registrados com `logger.warning`, incluindo o contexto do gráfico, e não são reemitidos.
- Em seguida, aplica margens conservadoras com `fig.subplots_adjust(left=0.14, right=0.94, top=0.90, bottom=0.22)`.
- Outros `UserWarning` são reemitidos, preservando o comportamento anterior.
- Falhas ao aplicar layout ou margens são registradas com `logger.exception` e não interrompem o desenho.

Todos os renderizadores passam a usar o helper, mantendo o `pad=0.4` onde já existia. Não é necessário alterar cache, payloads, contratos ou o orçamento de testes de UI.

Alternativa rejeitada: apenas filtrar o aviso com `warnings.filterwarnings`. Isso esconderia o problema sem registrar a ocorrência nem garantir margens utilizáveis.

### 7. Feedback de carregamento em Câmbio e Reserva

As duas sub-abas seguem o mesmo padrão do Tesouro Direto:

- Um `ttk.Label` com `Processando as informações. Aguarde…` fica centralizado atrás do painel do gráfico com `place`/`lower()`.
- Ao selecionar ou reexibir a sub-aba, o painel é ocultado antes da leitura do cache e do desenho; ao acionar `Atualizar`, permanece oculto durante a busca, o processamento e o desenho.
- Em `_finish_load`, `update_loading_state(False)` é aplicado antes de `_draw`; o painel só volta depois do desenho e de um `draw_idle()` adicional.
- Em falha, o painel é restaurado no `finally` e a mensagem de erro continua na statusbar.
- Na troca de ativo ou de janela, o painel permanece visível e apenas o ponteiro de espera é usado.
- O progresso indeterminado vive em um host fixo de 140 px; o rótulo de status usa `width=1` com `fill=X, expand=True`.
- `CambioOuroTab` cria um aviso de construção oculto por frame de sub-aba, mostra-o antes da construção, força a pintura com `update_idletasks()` e o remove ao final.

Se o serviço não estiver configurado, a sub-aba volta a exibir o painel em vez de deixá-lo oculto. O helper `BUSY_TEXT` e o `BusyIndicator` já existentes são reutilizados.

Alternativa rejeitada: duplicar o texto em cada sub-aba sem esconder o painel. Isso manteria o conteúdo parcial visível e o comportamento inconsistente com o Tesouro Direto.

### 8. Renomeação da aba

A aba de nível superior passa a ser registrada como `Câmbio e Reserva` em `shell.py`. No resumo de funcionalidades, a linha principal de interface usa `Dólar e Ouro`, enquanto a linha descritiva do mercado usa `Câmbio e Reserva`; `application/about.py`, `README.md` e a seção `Funcionalidades` da aba Sobre compartilham exatamente esse texto. O identificador interno `CAMBIO_TAB_ID` e os identificadores das sub-abas não mudam.

Alternativa rejeitada: manter nomes divergentes entre a aba, README e aba Sobre. Isso perpetua a inconsistência que o teste de paridade do resumo passou a detectar.

## Risks / Trade-offs

- [Gráficos ocultos durante o processamento] → o usuário vê o texto fixo em vez de conteúdo parcial; os painéis voltam após o desenho, inclusive em caso de falha.
- [`update_idletasks()` em callbacks do Tk pode reentrar em eventos] → chamar uma vez, após mostrar o texto/cursor e antes do trabalho pesado.
- [Contagem de referência por janela pode vazar] → indicadores simétricos, tolerância a janela destruída e estado descartado quando a raiz deixa de existir.
- [Cursor recursivo percorre a árvore] → árvore pequena e custo apenas ao entrar/sair ou reaplicar após a construção.
- [Teste de paridade do README é sensível a formatação] → comparar texto normalizado e extrair apenas a seção entre cabeçalhos de nível 2.
- [Margens de fallback podem ficar apertadas em figuras muito pequenas] → o fallback evita o aviso e mantém o desenho; ajustes finos continuam possíveis por gráfico.
- [Avisos de layout podem se repetir a cada redesenho] → cada ocorrência é registrada com contexto para diagnóstico; o log diário existente faz a retenção.
- [Ocultar o painel de mercado/reservas pode parecer travamento] → o texto fixo e o ponteiro de espera comunicam o processamento; o painel volta após o desenho.
- [Renomear a aba pode quebrar textos externos] → o identificador interno é preservado; README, aba Sobre e testes são atualizados junto.

## Migration Plan

Não há migração de dados. A mudança afeta a apresentação da GUI, o layout dos gráficos, o nome da aba e a documentação; reverter significa remover o texto fixo, o controle de visibilidade dos painéis, o resumo, o helper de layout e restaurar o nome anterior da aba.
