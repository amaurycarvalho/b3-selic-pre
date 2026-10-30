# Design

## Context

Ver `proposal.md` para a motivação. O estado da sub-aba já é calculado por `TesouroAnaliseViewModel` e `TesouroAnaliseController`, ambos headless; a GUI apenas aplica `status_text`/`status_kind` e desenha o placeholder. Hoje o view-model decide o texto nesta ordem: erro, carregando, sem dados, dados. A disponibilidade de cache é calculada uma vez em `on_show`, e o loader não expõe etapa alguma.

## Goals / Non-Goals

**Goals:**

- Corrigir a precedência de estados para que carga em andamento sempre prevaleça sobre erro antigo e sobre o aviso de cache vazio.
- Refletir cache preenchido por outra sub-aba sem reiniciar o aplicativo.
- Comunicar origem (cache/rede) e etapa corrente da atualização na statusbar.
- Manter toda a decisão de mensagem no view-model headless e testável sem Tkinter.

**Non-Goals:**

- Adicionar progresso determinado ao Tesouro; a barra permanece indeterminada.
- Alterar o contrato de cache em disco, os clientes HTTP ou a política de TTL.
- Notificar sub-abas irmãs em tempo real; a reavaliação ocorre ao reexibir a sub-aba.
- Aumentar o orçamento de testes de UI.

## Decisions

### 1. Estado de carga no controller/view-model, não na GUI

Adicionar ao controller os campos `loading_origin` (`"cache"` ou `"network"`), `loading_stage` e `error_context`. `begin_load(cache_only=...)` limpa o erro anterior e define a origem; `load()` reutiliza esse método. O view-model monta o texto:

- carregando do cache: `Lendo dados do Tesouro no cache…`;
- carregando da rede: `Atualizando dados do Tesouro…` com sufixo `(vendas|resgates|estoque)` quando houver etapa;
- carregando sem origem conhecida: mantém `Carregando dados do Tesouro…`.

`status_kind` retorna `info` para qualquer carga, nunca `warning`. `placeholder_message` retorna o texto de carregamento sempre que `loading` for verdadeiro. Alternativa rejeitada: montar essas strings na GUI; duplicaria regra e impediria testes headless.

### 2. Precedência explícita: carga > erro > vazio > dados

`status_text` verifica `loading` antes de `error`. O erro só reaparece após a nova tentativa falhar. Alternativa rejeitada: limpar o erro apenas em `_start_load`; o controller continuaria inconsistente quando usado diretamente e o erro voltaria a aparecer entre o início da thread e a primeira atualização de estado.

### 3. Etapa via callback opcional no loader, compatível com o contrato atual

`make_loader` passa a aceitar um `stage_callback` opcional e o invoca antes de cada operação sequential: `vendas`, `resgates`, `estoque`. `TesouroAnaliseController.load` aceita o callback e o repassa somente quando informado, preservando loaders de duas posições já usados em testes. A GUI marshala cada etapa para a thread da UI com `root.after` e reaplica o view-model.

Alternativa rejeitada: criar um novo protocolo de loader com objeto de progresso; seria mais invasivo sem ganho observável, já que a barra continua indeterminada.

### 4. Reavaliação de cache por método headless do controller

Adicionar `note_cache_presence(cache_present: bool) -> bool` ao controller: atualiza `cache_available`, calcula se o cache ficou disponível desde a última verificação e retorna verdadeiro apenas quando há dados a carregar, nenhuma carga em andamento e o cache passou de ausente para presente. A GUI chama esse método ao reexibir a sub-aba sem dados e, se retornar verdadeiro, inicia uma leitura `cache_only`.

Alternativa rejeitada: evento/broadcast entre sub-abas; acoplaria as sub-abas e não cobriria cache preenchido pela CLI ou por outra sessão.

### 5. Falha de leitura de cache tem contexto próprio

Quando `load(cache_only=True)` levanta exceção, o controller grava `error` e `error_context = "ler o cache"`; o view-model renderiza `Erro ao ler o cache: …`. Cache miss continua não sendo erro. Alternativa rejeitada: reutilizar `Erro ao carregar`, que não distingue corrupção/falha de leitura de ausência de cache.

## Risks / Trade-offs

- [Callback de etapa chamado fora da thread da UI] → a GUI sempre usa `root.after`, ignora callbacks após `_closed`/`_root_alive` falso e trata exceções de agendamento.
- [Reavaliação a cada reexibição pode iniciar leituras repetidas] → só dispara quando o cache passa de ausente para presente e não há dados nem carga em andamento.
- [Mensagens novas quebram testes existentes de texto exato] → atualizar os testes headless para o novo contrato, mantendo o mesmo orçamento de UI.
- [Etapa pode ficar defasada se várias etapas forem emitidas antes da UI processar a fila] → o stage é aplicado pelo valor capturado no `root.after`; a última etapa sempre corresponde ao estado final da atualização.
- [Barra indeterminada não informa fração concluída] → aceito; o contrato atual do Tesouro exige apenas progresso indeterminado e o texto de etapa cobre a comunicação.
