# Proposal

## Why

Spike realizado em 2026-10-30: o dataset CKAN `estoque-do-tesouro-direto` tinha a maior data em `2026-08` (metadados atualizados em 2026-10-16), enquanto o Balanço do Tesouro Direto (BTD) de setembro já estava publicado em 2026-10-29 com o estoque de `2026-09`. O BTD entrega a posição mensal por título em R$ milhões, exatamente os campos consumidos pela sub-aba `Estoque`, mas não entrega vencimento, PU nem quantidade. Ele deve complementar o CKAN nos meses mais recentes, não substituí-lo.

## What Changes

- Novo adaptador da publicação BTD: descobre a edição mais recente na página de publicações, localiza o anexo XLSX e lê a aba `2.1 - Estoque por Título`.
- Normalização do estoque por título/mês/valor do BTD para um modelo agregado, com cache próprio, gravação atômica e TTL curto (publicação mensal, mas revalidada diariamente).
- Política de sobreposição: ao atualizar a sub-aba `Estoque`, meses do BTD posteriores ao maior mês do CKAN são acrescentados; meses já existentes no CKAN NÃO SHALL ser substituídos.
- Leitura offline do cache BTD junto do cache CKAN, sem rede na primeira exibição.
- Falha do BTD NÃO SHALL falhar o refresh do CKAN; a sub-aba continua com os dados anteriores e informa a indisponibilidade de forma não bloqueante.
- A série analítica de estoque e a data-base passam a considerar o mês mais recente do CKAN ou do BTD, e a invalidação do cache analítico considera o hash da sobreposição.
- O status da sub-aba `Estoque` distingue quando a fonte complementar BTD contribuiu com um mês mais recente.
- O dataset CKAN, o modelo detalhado (`vencimento`, `PU`, `quantidade`), a CLI `tesouro-estoque` e os demais consumidores de estoque permanecem inalterados.

## Capabilities

### New Capabilities

- `tesouro-estoque-btd`: descoberta da publicação BTD, download e parsing do XLSX, cache normalizado, política de sobreposição de meses recentes e comportamento fail-soft.

### Modified Capabilities

- `tesouro-analise-gui`: a sub-aba `Estoque` lê e atualiza a sobreposição BTD, mostra a data-base mais recente e comunica a fonte/etapa sem bloquear o restante da aba.
- `tesouro-analise`: o pré-cálculo e a invalidação da série de estoque passam a considerar a sobreposição BTD, mantendo a retenção ancorada na maior data disponível.

## Impact

- Novo módulo de infraestrutura para a página BTD e o XLSX; parsing com a biblioteca padrão (`zipfile` + XML), sem dependência nova.
- Novo modelo agregado em `domain` e função de merge em `application/tesouro`, mantendo `EstoqueTesouroDireto` intacto para o CKAN/CLI.
- Ajustes em `presentation/tesouro_loaders.py`, `tesouro_precompute.py`, controller e view-model para a sub-aba `Estoque`.
- Novo arquivo de cache bruto normalizado e inclusão do seu hash nas dependências da partição analítica `estoque`.
- Testes headless de parsing XLSX, descoberta, cache, merge, invalidação e status; nenhum aumento do orçamento de testes de UI.
- Rede adicional apenas no refresh da sub-aba `Estoque` (ou após TTL), nunca na primeira exibição.
- A publicação BTD é HTML + XLSX; o adaptador fará parsing restrito da página para localizar o anexo, sem scraping de conteúdo além do necessário.
