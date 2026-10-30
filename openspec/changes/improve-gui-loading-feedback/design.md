# Design

## Context

Ver `proposal.md` para a motivação. Hoje a aba Tesouro Direto constrói a sub-aba de forma síncrona no primeiro `<<NotebookTabChanged>>` e só depois inicia a leitura do cache em background. A leitura leva cerca de 0,5 s e cada gráfico leva de 0,3 s a 1,5 s para ser montado/desenhado na thread da UI. O aviso atual aparece como conteúdo dos gráficos ou como overlay sobre eles, o que pode deixar resíduos e deslocar o layout.

As sub-abas Dólar e Ouro e Reservas Internacionais carregam em background, mas não usam o ponteiro de espera. A aba Sobre usa um `Text` somente leitura; o resumo de funcionalidades ainda não existe no README nem na interface.

## Goals / Non-Goals

**Goals:**

- Mostrar um texto fixo atrás dos gráficos enquanto o conteúdo não está pronto.
- Ocultar os gráficos durante a seleção da sub-aba e durante `Atualizar`.
- Reexibir os gráficos somente depois que a carga de dados e o desenho terminarem.
- Manter ponteiro, statusbar e progresso indicando o processamento.
- Evitar deslocamentos de layout ao ocultar/reexibir gráficos ou ao mostrar a barra de progresso.
- Publicar um resumo único de funcionalidades no README e na aba Sobre.

**Non-Goals:**

- Otimizar o tempo de montagem/desenho ou mover matplotlib para outra thread.
- Alterar cache, TTL, clientes HTTP, payloads ou contratos de dados.
- Adicionar progresso determinado às sub-abas.
- Mudar o comportamento de `Atualizar` além de ocultar/reexibir os gráficos.
- Renomear a aba `Câmbio e Ouro` ou corrigir a divergência de nomenclatura com o README.

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

## Risks / Trade-offs

- [Gráficos ocultos durante o processamento] → o usuário vê o texto fixo em vez de conteúdo parcial; os painéis voltam após o desenho, inclusive em caso de falha.
- [`update_idletasks()` em callbacks do Tk pode reentrar em eventos] → chamar uma vez, após mostrar o texto/cursor e antes do trabalho pesado.
- [Contagem de referência por janela pode vazar] → indicadores simétricos, tolerância a janela destruída e estado descartado quando a raiz deixa de existir.
- [Cursor recursivo percorre a árvore] → árvore pequena e custo apenas ao entrar/sair ou reaplicar após a construção.
- [Teste de paridade do README é sensível a formatação] → comparar texto normalizado e extrair apenas a seção entre cabeçalhos de nível 2.

## Migration Plan

Não há migração de dados. A mudança só afeta a apresentação da GUI e a documentação; reverter significa remover o texto fixo, o controle de visibilidade dos painéis e o resumo.
