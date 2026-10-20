## Context

Ver `proposal.md` para a motivação. O ponto de partida relevante:

- `launch_gui()` cria o `Tk` e em seguida constrói `SelicPreApp`, que monta toda a árvore de widgets de forma síncrona. A janela só recebe a primeira pintura quando `mainloop()` começa, depois do build.
- Medições locais (Xvfb) da construção do app: ~1,9 s com caches quentes e ~8,6 s na primeira execução, incluindo a montagem do cache de fontes do matplotlib. O import do backend `matplotlib.backends.backend_tkagg` sozinho leva ~0,87 s.
- Em Tk, irmãos criados depois ficam acima dos anteriores. Um `Frame` criado antes da barra superior fica coberto por ela até receber `lift()`.
- `Tooltip` cria um `Toplevel`; `lift()` no escudo não o cobre. `root.lift()` cobre no X11 testado, mas sobe a janela inteira acima de outros aplicativos e não é portátil.
- O orçamento de testes de UI está em 5 e cheio; `presentation/gui/*` é omitido de cobertura e mutação. Testes novos de Tk não são uma opção.

## Goals / Non-Goals

**Goals:**

- Pintar o escudo antes do trabalho pesado, para que ele seja realmente visível durante a inicialização.
- Garantir cobertura total, incluindo widgets criados depois do escudo.
- Bloquear ponteiro, teclado, foco e atalhos durante o escudo.
- Impedir tooltips acima do escudo por construção, sem depender de z-order.
- Encerrar o escudo de forma limpa, sem vazar eventos enfileirados para os controles.

**Non-Goals:**

- Translucidez ou animação; `ttk` não oferece alpha por widget e uma janela translúcida reintroduziria o problema de z-order.
- Cobrir a barra de título do sistema operacional.
- Introduzir carregamento de dados na inicialização.
- Alterar o estado de carregamento de buscas, o comportamento normal de tooltips ou o layout da barra superior.
- Adicionar dependências ou testes de UI novos.

## Decisions

### Escudo como `Frame` filho do root

Criar um `ttk.Frame` filho direto do root, com um `ttk.Label` centralizado via `place(relx=0.5, rely=0.5, anchor="center")`. O frame usa o fundo do tema (`#d9d9d9` no tema atual) e é opaco.

Alternativas consideradas:

- `Toplevel` com `-alpha`: permitiria translucidez, mas exigiria sincronizar posição/tamanho com o root e não resolveria tooltips acima sem `-topmost`/`root.lift()`, que são intrusivos.
- `Canvas` com stipple: simula translucidez, mas piora a legibilidade da mensagem e adiciona complexidade sem benefício.

### Criar o escudo dentro de `SelicPreApp.__init__`, antes do build

Ordem planejada:

1. `_load_icons()` (título), `_setup_state()`, `_apply_saved_settings()` (geometria) e o bind de `<Configure>`.
2. Criar o escudo, `place(relwidth=1, relheight=1)`, `lift()` e `root.update_idletasks()`.
3. Construir barra superior, opções, gráfico, toolbar e statusbar.
4. `lift()` novamente no escudo.
5. Agendar o encerramento e deixar `mainloop()` começar em `launch_gui`.

Isso mantém a lógica de geometria onde ela já vive e evita duplicar configuração de janela no composition root. `update_idletasks()` pinta o escudo sem processar eventos de entrada; foi validado empiricamente que a janela fica mapeada e o frame é desenhado.

Alternativa considerada: mover a criação do escudo para `launch_gui` e construir o app depois. Foi rejeitada porque a geometria salva é aplicada pelo app; o escudo apareceria no tamanho padrão antes de o app redimensionar a janela, ou exigiria duplicar/extrair `_apply_saved_settings`.

### Cobertura e z-order

`place(relwidth=1, relheight=1)` acompanha redimensionamentos do root sem lógica extra. O `lift()` é chamado imediatamente após o `place()` e novamente depois de toda a construção, porque os irmãos criados depois (barra superior, painel, toolbar, statusbar) ficam acima do escudo por padrão. O `DateEntry` do tkcalendar é um widget composto, mas está dentro da barra superior; o `lift()` do frame cobre o conjunto.

### Encerramento com settle de 200 ms

No fim do `__init__`, agendar `root.after(200, self._finish_startup)`. O timer só é executado depois que `mainloop()` começa, dando tempo para eventos enfileirados durante o build síncrono serem processados com o escudo ainda no topo. Não há espera mínima artificial além desse settle.

Alternativas consideradas:

- `after_idle`: pode ser adiado indefinidamente se houver fluxo contínuo de eventos; o timer é mais previsível.
- Encerrar o escudo ainda dentro do `__init__`: faria com que cliques enfileirados durante o build pudessem cair nos controles recém-revelados.
- `root.update()` após o build para drenar eventos: reentrante e arriscado, porque o protocolo de fechamento só é instalado depois da construção do app.

O valor de 200 ms fica em uma constante do módulo de escudo, para ajuste posterior sem espalhar números mágicos.

### Bloqueio total de interação

- O frame do escudo recebe `focus_set()` depois de ficar visível e tem `takefocus` habilitado.
- O escudo trata `<KeyPress>`, `<Tab>`, `<Shift-Tab>` e `<ISO_Left_Tab>` retornando `"break"`, impedindo foco e atalhos de chegarem aos controles.
- `_setup_shortcuts()` e `_setup_tooltips()` deixam de ser chamados no `__init__` e passam a ser chamados em `_finish_startup()`. Atalhos registrados só depois do encerramento também impedem que teclas enfileiradas durante o build disparem ações ao iniciar o `mainloop`.
- Os widgets em `_lockable_widgets` são desabilitados ao final do build e restaurados por `_update_button_states()` no encerramento. Ponteiro é bloqueado pela própria cobertura do escudo; o botão de fechar da janela continua funcionando porque a cobertura é interna ao cliente.

Alternativa considerada: manter atalhos registrados e adicionar uma flag de startup em cada handler. Foi rejeitada por espalhar condicionais por ações independentes e deixar caminhos esquecidos.

### Tooltips suprimidos por adiamento

Como `_setup_tooltips()` só roda no encerramento, nenhum `Tooltip` existe durante o escudo, portanto nenhum `Toplevel` pode aparecer acima dele. Não é necessário um gate de suspensão para um evento único de inicialização.

Alternativa considerada: criar os tooltips no build e manter um `TooltipGate` compartilhado. Seria reutilizável para futuros overlays, mas adiciona estado e testes sem necessidade neste escopo.

### Encerramento e restauração

`_finish_startup()` deve:

1. Destruir o frame do escudo e limpar a referência.
2. Restaurar os controles lockable via `_update_button_states()`.
3. Registrar atalhos e tooltips.
4. Deixar a mensagem inicial da statusbar visível (ela já foi definida em `_setup_state`).
5. Não alterar o foco além do necessário; após destruir o escudo, o Tk volta o foco para o root.

O callback deve ser tolerante a root já destruído (por exemplo, checar `winfo_exists()` antes de operar), para não gerar erro durante o fechamento.

### Visual

Apenas texto centralizado, sem ícone, spinner ou barra de progresso. Como o build é síncrono, qualquer animação ficaria congelada justamente durante a maior parte da espera.

## Risks / Trade-offs

- [Pintura do escudo pode variar por plataforma] → `update_idletasks()` foi validado no X11; a verificação manual deve cobrir Linux e, se possível, Windows. Se necessário, o fallback é chamar `update()` com um protocolo de fechamento temporário.
- [Eventos enfileirados podem escapar se o settle for curto] → 200 ms com foco no escudo, atalhos adiados e controles desabilitados; o valor é centralizado para ajuste.
- [Build síncrono muito longo pode fazer o SO marcar a janela como "não respondendo"] → o escudo comunica a espera, mas não resolve o bloqueio da thread; mover o build para outra thread está fora de escopo.
- [Atalhos e tooltips não existem se o app for construído sem `mainloop()`] → uso esperado é a GUI via `launch_gui()`; os testes atuais não dependem desses registros durante a construção.
- [Callbacks de geometria agendados (`center`, `zoomed`, sidebar) rodam durante o settle] → o `place` relativo acompanha qualquer redimensionamento e o escudo permanece no topo.
- [Referência ao escudo mantida após o encerramento] → `_finish_startup()` limpa a referência e o callback verifica a existência do root.

## Migration Plan

Não há migração de dados ou API. O rollback consiste em remover a criação/agendamento do escudo e voltar a chamar `_setup_shortcuts()` e `_setup_tooltips()` no `__init__`.
