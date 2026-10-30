# Proposal

## Why

A statusbar das sub-abas do Tesouro Direto mistura estados incompatíveis. Sem cache, ao clicar em `Atualizar` ela continua exibindo "Nenhum dado em cache. Pressione Atualizar para carregar."; depois de uma falha, uma nova tentativa mantém o erro antigo em vermelho enquanto a carga corre; e a disponibilidade de cache é verificada uma única vez por sub-aba, então o aviso fica obsoleto quando outra sub-aba preenche o cache. O usuário não consegue distinguir leitura de cache, download e etapa em andamento, o que torna a atualização ambígua.

## What Changes

- Priorizar o estado de carregamento sobre erro antigo e sobre a orientação de cache vazio na statusbar e no texto centralizado dos gráficos.
- Limpar o erro anterior no início de cada carga, para que uma nova tentativa mostre progresso em vez da falha antiga.
- Reavaliar a disponibilidade de cache a cada exibição da sub-aba, permitindo que dados gravados por outra sub-aba sejam reconhecidos sem reiniciar o aplicativo.
- Distinguir na statusbar a leitura de cache da atualização de rede, informando a etapa corrente (`vendas`, `resgates`, `estoque`) durante o refresh.
- Tratar falha inesperada de leitura de cache como aviso explícito, em vez de reportá-la como ausência de dados.
- Manter a barra de progresso indeterminada e a desabilitação dos controles conforme o contrato atual, sem adicionar progresso determinado ao Tesouro.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `tesouro-analise-gui`: estados de carregamento, cache e status da sub-aba passam a refletir corretamente refresh sem cache, nova tentativa após erro, cache disponível após outra sub-aba e etapa corrente da atualização.

## Impact

- `presentation/tesouro_analise_view_model.py`: precedência de estado e mensagens de status/placeholder.
- `presentation/tesouro_analise_controller.py`: limpeza de erro e estado de etapa da carga.
- `presentation/tesouro_loaders.py` e `presentation/gui/tesouro_sub_tab.py`: reavaliação de cache, callback de etapa e tratamento de falha de leitura.
- Testes headless de view-model, controller e loaders; nenhum aumento do orçamento de testes de UI.
- Sem novas dependências, mudanças de contrato de dados ou alterações de cache em disco.
