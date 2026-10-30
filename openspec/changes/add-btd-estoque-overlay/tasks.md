# Tasks

## 1. Modelo e merge headless

- [ ] 1.1 Criar `EstoqueMensalTitulo` em `domain/models.py` com `tipo_titulo`, `mes` e `valor_estoque` imutáveis; verificar com teste de criação e igualdade.
- [ ] 1.2 Criar a função de merge em `application/tesouro` que adiciona ao estoque do CKAN apenas pares `(tipo_titulo, mes)` ausentes do BTD e nunca substitui os existentes; verificar com testes de mês novo, mês coincidente, BTD vazio e título desconhecido.
- [ ] 1.3 Adaptar `build_estoque_snapshot`/`TesouroSeriesProvider` para aceitar um protocolo estrutural de estoque com `tipo_titulo`, `mes` e `valor_estoque`; verificar que os testes existentes de séries continuam passando.

## 2. Infraestrutura BTD

- [ ] 2.1 Implementar a descoberta da edição BTD mais recente a partir da página de publicações, extraindo mês de referência, data de publicação e link do anexo XLSX; verificar com fixture HTML de setembro/2026 e com página sem anexo.
- [ ] 2.2 Implementar o download do anexo com validação de `Content-Type`/assinatura ZIP e preservação do conteúdo anterior em falha; verificar com testes de sucesso, 404, corpo inválido e timeout.
- [ ] 2.3 Implementar o parsing XLSX com `zipfile`/XML, identificando a aba `ANEXO 2.1 - ESTOQUE POR TÍTULO`, lendo apenas a seção em R$ milhões e convertendo `Set/26` para `2026-09`; verificar com fixture XLSX mínimo e com caso de percentuais que não devem ser lidos como valores.
- [ ] 2.4 Implementar cache normalizado atômico em `estoque-btd.json` com metadados de proveniência e TTL de 24h; verificar com testes de cache fresco, vencido, gravação atômica e leitura somente cache.
- [ ] 2.5 Garantir que falha do BTD nunca propague como falha global do refresh e que o cache anterior permaneça legível; verificar com testes de exceção em cada etapa (descoberta, download, parsing).

## 3. Integração com a série analítica

- [ ] 3.1 Adicionar dependência opcional do arquivo BTD em `source_hashes`/`RAW_FILES` com sentinela estável para ausência; verificar que a partição `estoque` não invalida quando o arquivo nunca existiu e invalida quando ele muda/aparece/desaparece.
- [ ] 3.2 Fazer o pré-cálculo da série `estoque` usar o merge CKAN+BTD e ancorar a data-base/retenção no mês mais recente; verificar com testes de mês BTD mais novo, sem sobreposição e retenção de 3 anos.
- [ ] 3.3 Garantir que `demanda` e `fluxo` não sejam recalculados quando só a sobreposição BTD muda; verificar com teste de invalidação seletiva.

## 4. Integração com a sub-aba Estoque

- [ ] 4.1 No loader de `KIND_ESTOQUE`, buscar o CKAN, tentar atualizar o BTD de forma best-effort e montar `AnaliseData` com o merge; verificar com testes de sucesso, BTD sem novidade e falha do BTD mantendo o CKAN.
- [ ] 4.2 Na leitura `cache_only`, ler o cache BTD junto do CKAN e montar o mesmo merge sem rede; verificar com teste de dois caches presentes, apenas CKAN e apenas BTD.
- [ ] 4.3 Propagar a sobreposição para o pré-cálculo e para o view-model, ajustando data-base e status quando o BTD contribui ou falha; verificar com testes headless de controller/view-model.
- [ ] 4.4 Garantir que `Apetite do mercado`, a CLI `tesouro-estoque` e o dataset CKAN permaneçam inalterados; verificar com os testes existentes de CLI e carregamento.
- [ ] 4.5 Adicionar a mensagem de falha não bloqueante do BTD ao status da sub-aba sem impedir a atualização do CKAN; verificar com teste de view-model/controller e teste manual.

## 5. Validação

- [ ] 5.1 Executar `make lint` e verificar que termina sem erros.
- [ ] 5.2 Executar `make complexity` e verificar que termina sem violações.
- [ ] 5.3 Executar os testes relacionados (`tests/test_tesouro_*`, `tests/test_tesouro_analise_*`, `tests/test_tesouro_datasets_cli.py`) e verificar que todos passam.
- [ ] 5.4 Teste manual opcional: abrir a sub-aba `Estoque` com cache CKAN antigo e cache BTD de setembro/2026; confirmar que o gráfico mostra `2026-09` e que `Visão geral` compara o mesmo mês.
- [ ] 5.5 Teste manual opcional: simular falha do BTD (URL inválida) e confirmar que o refresh do CKAN continua, a sub-aba segue utilizável e o status informa a falha não bloqueante.

## Workflow follow-up

- Se `fix-tesouro-status-feedback` ainda não estiver implementada, alinhar a mensagem de falha não bloqueante com o contrato de status daquela change para evitar dois formatos de aviso.
- Arquivar esta change somente após a spec principal de `tesouro-estoque-btd` existir e os deltas de `tesouro-analise-gui` e `tesouro-analise` terem sido aplicados.
