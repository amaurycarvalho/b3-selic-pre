## 1. Infraestrutura de cache, settings e lock

- [x] 1.1 Adicionar leitura somente leitura ao cache, sem remover entradas inválidas/vencidas, e cobrir com testes de cache corrompido, incompleto e miss sem rede
- [x] 1.2 Tornar a escrita do cache atômica com arquivo temporário e `os.replace`, preservando a validação de completude, e cobrir com teste de leitura concorrente
- [x] 1.3 Adicionar a chave `data_referencia` aos defaults de settings e cobrir leitura de arquivo ausente, corrompido e sem a chave
- [x] 1.4 Tornar a gravação de settings atômica e cobrir com teste de leitura durante escrita
- [x] 1.5 Implementar lock de ação em infraestrutura com `fcntl`/`msvcrt`, timeout e mensagem de espera, e cobrir com testes de aquisição, liberação e timeout
- [x] 1.6 Integrar o lock ao subcomando `atualizar` e garantir liberação em falha, com teste de ordem de eventos
- [x] 1.7 Persistir `data_referencia` em `atualizar`, na preparação do MCP e no sucesso de carga da GUI, sem alterar em `consultar`/`exportar`, e cobrir com testes por caminho

## 2. Aplicação: análise curta e longa

- [x] 2.1 Implementar a transformação pura de curva bruta para taxa média por ano e a transformação do histórico, com teste de múltiplos anos e datas vazias
- [x] 2.2 Adicionar a representação aos construtores de texto de análise e evolução, convertendo curva e histórico quando `longa`, com teste de inclinação baseada em médias
- [x] 2.3 Adicionar `analise_curva` à seleção de artefatos de exportação, mantendo `curta` como padrão, com teste dos artefatos `curta`, `longa` e `ambas`
- [x] 2.4 Implementar o contrato opcional de análise pré-calculada com verificação de representação, recalculando quando a representação não coincide, com teste de não reutilização cruzada
- [x] 2.5 Garantir que os serviços de análise permaneçam sem imports de `presentation`/`infrastructure`, com teste de arquitetura

## 3. Aplicação: payloads do MCP

- [x] 3.1 Criar os serviços headless de payload para curva, exportação, análise, evolução, estatísticas e datas, com testes de formato e valores numéricos
- [x] 3.2 Implementar o envelope de erros de domínio com `motivo`, `detalhe` e `dica`, com testes para `data_invalida`, `data_futura`, `data_antiga`, `sem_dados` e `cache_vazio`
- [x] 3.3 Implementar cursores opacos e paginação para curva, evolução, datas e catálogo, com testes de continuação, fim e cursor inválido
- [x] 3.4 Garantir que os serviços de payload não importem `presentation`, `infrastructure`, rede ou UI, com teste de pureza

## 4. Protocolo e servidor MCP

- [x] 4.1 Implementar constantes, códigos de erro, validação de `_meta`, envelope `resultType` e `serverInfo`, com testes de requisição válida e metadados ausentes
- [x] 4.2 Implementar `server/discover`, rejeição de versão não suportada com `-32022` e rejeição de `initialize` nomeando a versão suportada, com testes de cada resposta
- [x] 4.3 Implementar o loop `stdio` com leitura por linha, EOF, pool de workers, escrita serializada e captura/redirecionamento de `stdout`, com teste de pureza de stdout e encerramento
- [x] 4.4 Implementar dispatcher de `tools/list` e `tools/call`, incluindo tool desconhecida e parâmetros inválidos, com testes de erro `-32602` e `-32601`
- [x] 4.5 Implementar cancelamento por `notifications/cancelled`, com teste de requisição cancelada sem resposta e cancelamento desconhecido ignorado
- [x] 4.6 Implementar tratamento de falha interna com `isError`, log em stderr e continuidade do servidor, com teste de duas chamadas consecutivas

## 5. Catálogo e tools

- [x] 5.1 Definir o catálogo determinístico, schemas de entrada e anotações de somente leitura, com teste do conjunto exato de oito tools
- [x] 5.2 Implementar `data_referencia` com settings, fallback de cache, `disponivel` e `cache_vazio`, com testes dos três caminhos
- [x] 5.3 Implementar `consultar_curva` para `curta` e `longa`, com paginação e erros de data, com testes de registros, consolidação e `sem_dados`
- [x] 5.4 Implementar `exportar_curva_curta` e `exportar_curva_longa` devolvendo CSV sem gravar arquivos, com testes de colunas, delimitador e datas indisponíveis
- [x] 5.5 Implementar `analise` com `curva` padrão `curta`, `longa` por médias anuais e datas indisponíveis, com testes de ambas as representações
- [x] 5.6 Implementar `evolucao` e `estatisticas` com indicadores resumidos e paginação, com testes de valores e `sem_dados`
- [x] 5.7 Implementar `listar_datas` com ordenação decrescente, metadados, paginação e lista vazia, com testes de cache vazio e múltiplas datas
- [x] 5.8 Integrar tools ao dispatcher e cobrir cada tool com um teste de chamada ponta a ponta pelo protocolo

## 6. CLI, preparação e composition root

- [x] 6.1 Adicionar o subcomando `mcp` com `--atualizar` e `--data`, rejeitando parâmetros não suportados, com testes de parser e ajuda
- [x] 6.2 Mover o import da GUI para dentro do ramo `gui`, com teste que importa a CLI em ambiente sem Tk/matplotlib
- [x] 6.3 Despachar `mcp` no composition root, injetando leitor de cache e settings, com teste de composição
- [x] 6.4 Extrair a carga compartilhada de `atualizar` e usá-la na preparação do MCP, com lock, progresso em stderr, liberação antes do loop e falha sem servidor
- [x] 6.5 Adicionar `exportar --analise-curva` com validação de dependência de `--analise` e independência de `--curva`, com testes de parser e comando
- [x] 6.6 Configurar logging do modo MCP apenas em stderr e impedir gravação no log ativo durante o atendimento, com teste de handlers e stdout
- [x] 6.7 Executar `tests/test_architecture.py` e confirmar que nenhuma nova exceção foi adicionada ao allowlist

## 7. Documentação

- [x] 7.1 Criar `docs/misc/mcp.md` com visão geral, protocolo `2026-07-28`, transporte, preparação, ciclo de vida, erros e cancelamento
- [x] 7.2 Documentar em `docs/misc/mcp.md` todas as tools, schemas, paginação, envelope de erros e non-goals
- [x] 7.3 Adicionar a `docs/misc/mcp.md` as duas seções Docker: imagem a partir do código fonte com `--no-deps` e imagem a partir do binário PyInstaller, incluindo build, run, volume de cache/config, `--network none` e configuração de cliente
- [x] 7.4 Atualizar `docs/misc/cli.md` com o subcomando `mcp`, `--atualizar`, `--data`, `--analise-curva` e exemplos
- [x] 7.5 Adicionar ao `README.md` uma seção breve sobre o servidor MCP apontando para `docs/misc/mcp.md`
- [x] 7.6 Revisar os exemplos de Docker e cliente MCP contra os comandos reais e confirmar que não há `-t` nem escrita em stdout

## 8. Validação final

- [x] 8.1 Executar `make lint` e corrigir todas as falhas
- [x] 8.2 Executar `make complexity` e corrigir todas as falhas
- [x] 8.3 Executar os testes diretamente relacionados: protocolo, tools, cache, settings, análise, CLI e preparação
- [x] 8.4 Executar a suíte completa (`make test`) por envolver CLI, cache, settings e contratos compartilhados
- [x] 8.5 Smoke test manual do protocolo: iniciar `b3-selic-pre mcp` com cache preparado, enviar `server/discover`, `tools/list` e `tools/call` por `stdin`, fechar `stdin` e confirmar respostas JSON-RPC e saída `0`
- [x] 8.6 Smoke test manual de Docker: construir a imagem de fonte, preparar o cache em um volume, rodar o atendimento com `--network none` e chamar `data_referencia` e `consultar_curva`
- [x] 8.7 Registrar como passo manual opcional para o usuário: configurar o servidor no cliente MCP e verificar `data_referencia`, `analise` curta/longa e `listar_datas`
