## Why

A aplicação hoje é uma janela única com a curva SELIC Pré. As changes de Tesouro Direto planejam uma janela separada (`Toplevel`) com tabelas, o que fragmenta a experiência e não acomoda a evolução futura para câmbio. O produto precisa de uma **janela única com abas por classe de ativo** e, dentro de Tesouro Direto, sub-abas de análise (estoque e apetite) com gráficos, não mais uma janela concorrente.

O carregamento lazy é necessário para manter o startup rápido: só a aba visível é construída; as demais são montadas na primeira exibição.

## What Changes

- Introduzir um shell de abas de nível superior com `SELIC Pré`, `Tesouro Direto` e o ponto de extensão para `Câmbio` (registrada na change futura).
- Manter `SELIC Pré` como a tela atual, inalterada, agora dentro de uma aba; ela permanece a aba padrão.
- Adicionar a aba `Tesouro Direto` com as sub-abas `Visão geral`, `Estoque` e `Apetite do mercado`.
- Em cada sub-aba, exibir dois gráficos: **percentual atual** e **evolução**, com seletor de janela 14d/3m/12m/3a. Na `Visão geral`, o gráfico atual compara estoque e apetite, e o de evolução mostra o gap entre eles.
- Carregar o conteúdo das sub-abas de forma lazy, na primeira vez que ficarem visíveis; abas ocultas NÃO SHALL ser construídas no startup.
- Ao exibir uma sub-aba pela primeira vez, ler apenas o cache analítico; se não houver cache, orientar “clique em Atualizar”, sem download automático.
- Oferecer “Atualizar” e “Ignorar cache” por sub-aba, com progresso indeterminado e status próprio.
- Remover do escopo das changes de vendas/resgates a janela `Toplevel` e as abas de tabelas; as tabelas brutas continuam apenas na CLI.
- Manter o título atual da janela até a change de Câmbio.
- **Non-goals:** conteúdo de câmbio, ouro, projeções, tabelas brutas no GUI, novos cálculos analíticos, alteração do gráfico principal SELIC Pré, exportação dedicada, MCP.

## Capabilities

### New Capabilities

- `app-tabs`: shell de abas de nível superior, registro de abas para extensão futura (`Câmbio`), preservação da aba SELIC Pré e carregamento lazy por visibilidade.
- `tesouro-analise-gui`: aba `Tesouro Direto` com sub-abas `Visão geral`, `Estoque` e `Apetite do mercado`, cada uma com gráfico de percentual atual, gráfico de evolução, seletor de janela, atualização e status.

### Modified Capabilities

<!-- Nenhuma capability principal muda de requisito; a tela SELIC Pré permanece inalterada. -->

## Impact

- Refatoração de `src/b3_selic_pre/presentation/gui/app.py` em shell + controllers de aba.
- Novos módulos de aba em `src/b3_selic_pre/presentation/gui/` e novos renderizadores em `src/b3_selic_pre/presentation/`.
- `GuiDependencies` e `launch.py` passam a compor os controllers de Tesouro e o registro de abas.
- As changes `add-tesouro-direto-vendas` e `add-tesouro-direto-resgates-estoque` perdem a GUI (botão/janela/abas) e mantêm dados + CLI.
- Depende de `add-tesouro-analise-percentuais` para as séries e percentuais.
- Testes de lazy/registro e view-models serão headless; os 5 testes de UI existentes serão adaptados, sem aumentar o orçamento.
- A suíte completa é justificada por envolver a janela principal, composição de dependências e contratos compartilhados.
