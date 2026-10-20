## Why

A janela principal só fica visível depois que toda a construção da interface termina — cerca de 2 s com cache quente e até ~9 s na primeira execução, quando o matplotlib ainda monta o cache de fontes. Nesse intervalo o usuário não recebe feedback algum e, quando a janela finalmente aparece, não há nada que impeça interação com controles que acabaram de ser criados. Um escudo de inicialização torna o tempo de espera explícito e garante que a aplicação só aceite interação quando estiver pronta.

## What Changes

- Exibir um escudo opaco cobrindo toda a área útil do toplevel desde antes da construção pesada da interface até a primeira renderização, com a mensagem centralizada "Aguarde a inicialização da aplicação…".
- Garantir a cobertura de todos os controles, inclusive a barra superior criada depois do escudo, reerguendo o escudo sobre os irmãos após a construção e mantendo a cobertura durante redimensionamentos.
- Bloquear totalmente a interação durante o escudo: ponteiro, teclado, Tab/foco e atalhos globais; apenas o fechamento da janela continua permitido.
- Impedir que tooltips da barra superior apareçam acima do escudo, registrando os tooltips somente após o término da inicialização.
- Encerrar o escudo após a construção da UI e a primeira renderização, aguardando um pequeno intervalo de acomodação para drenar eventos que tenham sido enfileirados durante o build; em seguida, restaurar o estado normal dos controles, atalhos e tooltips.
- Não alterar o comportamento de tooltips, atalhos ou do estado de carregamento de buscas depois da inicialização.

## Capabilities

### New Capabilities

- `startup-shield`: cobertura visual e bloqueio de interação durante a inicialização da GUI, incluindo mensagem de espera, garantia de z-order sobre a barra superior, supressão de tooltips e encerramento após a primeira renderização.

### Modified Capabilities

<!-- Nenhuma capacidade existente tem requisito alterado. A supressão de tooltips durante a inicialização é parte da nova capacidade; o comportamento normal de tooltips permanece inalterado. -->

## Impact

- `src/b3_selic_pre/presentation/gui/startup.py` (novo): frame de escudo, mensagem centralizada, bloqueio de teclado/foco e ciclo de exibição/encerramento.
- `src/b3_selic_pre/presentation/gui/app.py`: criação antecipada do escudo, `update_idletasks()` para pintá-lo antes do build, `lift()` final, adiamento de atalhos/tooltips e encerramento agendado.
- `src/b3_selic_pre/presentation/gui/actions.py`: mantém `_setup_shortcuts` e `_setup_tooltips`; apenas o momento de chamada muda.
- `tests/test_b3_selic_pre_gui.py`: continua sendo a cobertura de GUI existente; nenhum teste de UI novo é adicionado por causa do orçamento atual.
- Sem mudanças em `domain`, `application`, `infrastructure`, dependências externas ou formato de dados.
