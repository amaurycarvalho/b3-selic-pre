# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [rfc001-tesouro-direto-redesign](openspec/changes/rfc001-tesouro-direto-redesign/) Reprojetar a extração do Tesouro Direto com spike de descoberta como pré-requisito bloqueante

## [1.0.0] - 2026-10-20

### [add-about-dialog](openspec/changes/archive/2026-10-20-add-about-dialog/) A aplicação expõe versão apenas no título da janela e no `--version`, sem um local que reúna identidade, licença, apresentação e caminhos úteis para o usuário.

#### Added

- Adicionar um botão "Sobre" na barra superior, com o ícone `help-about.png`, à direita do botão de copiar dados e visualmente separado dos botões de busca e cópia. O botão terá tooltip.
- Abrir uma janela modal com ícone da aplicação, nome e versão (`Taxas Referenciais SELIC (B3) vX.Y.Z`), data de lançamento ISO, licença GNU GPLv3 e texto curto de apresentação.
- Incluir no diálogo botões para abrir o repositório no navegador padrão, o diretório de logs no gerenciador de arquivos padrão e um botão "Fechar" que encerra o diálogo.
- Introduzir `__release_date__` no pacote e atualizar a skill `release-version` para alterá-lo junto com a versão.
- Verificar a versão mais recente na API de releases do GitHub em background, na primeira abertura do diálogo, com cache por sessão. Quando houver versão mais nova, exibir o aviso "Nova versão vX.Y.Z disponível" e um botão para abrir a página da release. Falha, timeout ou resposta inválida não exibem aviso.
- Cobrir a lógica nova com testes headless, preservando o orçamento atual de testes de UI.

#### Changed

- Quando o diretório de logs não existir, informar a indisponibilidade dentro do próprio diálogo, sem criar o diretório e sem falhar silenciosamente.

### [add-application-logging](openspec/changes/archive/2026-10-19-add-application-logging/) A aplicação não possui logging: falhas de rede viram traceback no stderr (ou desaparecem no modo gráfico), não há histórico persistente por dia, nem retenção controlada.

#### Added

- Criar um subsistema de logging compartilhado por CLI e GUI, com registros formatados com data/hora local e gravados em arquivo diário.
- Introduzir o contrato `CommunicationError` na camada `application`; a infraestrutura mapeia a família de rede/HTTP vigente (hoje `urllib`; futuramente `requests`, em mudança separada).
- Registrar falhas de comunicação toleradas em uma única linha, com tipo e mensagem da exceção, sem call stack; registrar qualquer outra exceção com traceback completo.
- Instalar hooks de exceções não tratadas (`sys.excepthook`, `threading.excepthook` e `Tk.report_callback_exception`) para registrar defeitos inesperados com traceback.
- Reutilizar a base XDG/plataforma do cache para o diretório `.../b3-selic-pre/logs/`, em vez de duplicar a lógica de caminho.

#### Changed

- Configurar o formato via `format`/`datefmt` do `logging.basicConfig`, aplicando o mesmo formato a todos os handlers da aplicação.
- Rotacionar o arquivo ativo `b3-selic-pre.log` na virada do dia local para `b3-selic-pre-YYYY-MM-DD.log`, de forma preguiçosa no primeiro registro após a meia-noite.
- Na inicialização, rotacionar o arquivo ativo cuja data de modificação seja anterior ao dia local corrente, usando a data da última modificação; se o backup de destino existir, anexar o conteúdo e remover o ativo.
- Na inicialização da GUI, apagar backups datados anteriores a `hoje - N`, preservando o dia corrente e os `N` dias anteriores; nunca apagar o arquivo ativo nem nomes fora do padrão datado.
- Ler `N` de `log_retention_days` em `settings.json`, com padrão `7` e fallback para ausente, não inteiro, booleano ou menor que `1`.
- Aplicar o mesmo tratamento no boundary de fetch da GUI e da CLI. Na CLI, falhas de comunicação geram mensagem amigável em stderr e saída com código `1`; falhas não-comunicação registram traceback e são relançadas.

### [add-mcp-stdio-server](openspec/changes/archive/2026-10-20-add-mcp-stdio-server/) A aplicação já expõe a curva SELIC Pré por CLI e GUI, mas agentes externos não têm uma interface estruturada e somente leitura para consultar os mesmos dados.

#### Added

- Adicionar o subcomando `b3-selic-pre mcp`, com transporte `stdio` e encerramento em EOF.
- Implementar a revisão MCP `2026-07-28`: `_meta` por requisição, `server/discover`, `tools/list`, `tools/call`, `UnsupportedProtocolVersionError`, erros para `initialize` legado e cancelamento.
- Expor tools somente leitura: `data_referencia`, `consultar_curva`, `exportar_curva_curta`, `exportar_curva_longa`, `analise`, `evolucao`, `estatisticas` e `listar_datas`.
- Preparar dados opcionalmente na inicialização com `--atualizar` e `--data <AAAA-MM-DD>`, reutilizando a carga de `atualizar`, sob lock de ação, com progresso em `stderr` e sem iniciar o servidor em caso de falha.
- Persistir `data_referencia` no settings da aplicação, atualizado por `atualizar`, preparação do MCP e carga da GUI; `consultar` e `exportar` não alteram a referência.
- Permitir selecionar a análise da curva curta ou longa, com a curva longa definida pela taxa média por ano; adicionar `exportar --analise-curva curta|longa`.
- Documentar o servidor e as tools em `docs/misc/mcp.md`, incluindo execução em Docker a partir do código fonte e do binário PyInstaller, e registrar uma seção breve no `README.md`.

#### Changed

- Tornar a leitura do cache somente leitura no MCP e a escrita de cache/settings atômica.

### [add-startup-shield](openspec/changes/archive/2026-10-20-add-startup-shield/) A janela principal só fica visível depois que toda a construção da interface termina — cerca de 2 s com cache quente e até ~9 s na primeira execução, quando o matplotlib ainda monta o cache de fontes.

#### Added

- Exibir um escudo opaco cobrindo toda a área útil do toplevel desde antes da construção pesada da interface até a primeira renderização, com a mensagem centralizada "Aguarde a inicialização da aplicação…".
- Garantir a cobertura de todos os controles, inclusive a barra superior criada depois do escudo, reerguendo o escudo sobre os irmãos após a construção e mantendo a cobertura durante redimensionamentos.
- Bloquear totalmente a interação durante o escudo: ponteiro, teclado, Tab/foco e atalhos globais; apenas o fechamento da janela continua permitido.
- Impedir que tooltips da barra superior apareçam acima do escudo, registrando os tooltips somente após o término da inicialização.
- Encerrar o escudo após a construção da UI e a primeira renderização, aguardando um pequeno intervalo de acomodação para drenar eventos que tenham sido enfileirados durante o build; em seguida, restaurar o estado normal dos controles, atalhos e tooltips.

#### Changed

- Não alterar o comportamento de tooltips, atalhos ou do estado de carregamento de buscas depois da inicialização.

### [cli-subcommands](openspec/changes/archive/2026-10-20-cli-subcommands/) A CLI atual concentra data, visão, GUI, atalho, cache e versão em flags planas e não oferece caminhos para atualizar a evolução da curva, gerar o texto determinístico de análise ou exportar esses artefatos.

#### Added

- Adicionar `atualizar --data AAAA-MM-DD` (default: hoje), que carrega a curva de referência e a janela de evolução, gera o texto executivo e o texto de evolução da curva.
- Adicionar `exportar` com seleção de conteúdo: evolução curta, evolução longa, análise determinística e log atual da aplicação, com saída em stdout (um artefato) ou diretório (vários artefatos).

#### Changed

- **BREAKING** Reorganizar a CLI em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `gui` e `criar-atalho`.
- **BREAKING** Substituir `--visao` e `--evolucao` por um único `--curva curta|longa|ambas`.
- Manter `b3-selic-pre` sem argumentos abrindo a GUI; `gui` passa a ser o subcomando explícito equivalente.
- Registrar uma linha por invocação da CLI com comando, argumentos, início, fim, duração e código de saída, reutilizando formato e rotação diária do log da aplicação.
- Documentar os parâmetros em `docs/misc/cli.md` e adicionar uma seção resumida apontando para esse arquivo no `README.md`.
- Atualizar manifestos de atalho e referências de spec que ainda usam `--gui` ou `--create-shortcut`.

#### Removed

- **BREAKING** Remover a sintaxe antiga baseada em data posicional e flags `--today`, `--yearly`, `--gui`, `--create-shortcut`, `--no-cache` no nível raiz.

### [establish-architecture-governance](openspec/changes/archive/2026-10-19-establish-architecture-governance/) A aplicação já declara quatro camadas Clean Architecture, mas não há verificação automática das dependências entre elas.

#### Added

- Criar a capability de governança de arquitetura com regras explícitas de dependência entre `domain`, `application`, `infrastructure` e `presentation`.
- Adicionar testes de guarda que falham quando uma camada interna importa uma camada externa não aprovada.
- Introduzir um arquivo de aprovações explícitas (`tests/architecture_allowlist.py`) para dívidas conhecidas; novas exceções exigem alteração explícita nesse arquivo e revisão.
- Adicionar teste de guarda para pureza da camada `domain` e para ausência de dependências de UI/rede na camada `application`, viabilizando testes headless.
- Adicionar orçamento de testes de UI (UI test budget): todo teste que instancia Tk ou a aplicação GUI deve ser marcado com `@pytest.mark.ui`, a contagem não pode crescer e o orçamento só pode diminuir.

#### Changed

- Registrar `make lint`, `make complexity` e testes direcionados como validação obrigatória de toda change, reservando a suíte completa para mudanças com risco real de regressão.
- Definir no processo de change que, quando a suíte completa não for justificada, o último passo deve ser um teste manual opcional do usuário.

### [fix-csv-rate-loading](openspec/changes/archive/2026-10-19-fix-csv-rate-loading/) O carregamento da curva está vulnerável a respostas `200 OK` com corpo vazio da B3: o `GetDownloadFile` (CSV) e o `GetList` falham de forma intermitente, o resultado vazio/parcial é cacheado como se fosse válido e o gráfico pode ficar em branco ou lançar exceção.

#### Added

- Adicionar retry com backoff exponencial e jitter para respostas `200` com corpo vazio, tanto no CSV quanto no `GetList`, com até 6 tentativas e sem mascarar erros de schema.

#### Changed

- Centralizar a seleção de fonte: **hoje** usa `GetList`; **datas anteriores** usam `GetDownloadFile` como fonte primária, com `GetList` apenas como fallback após esgotar as tentativas do CSV.
- Validar completude do `GetList` por `page.totalRecords`/`page.totalPages`: buscar todas as páginas, repetir páginas vazias e falhar explicitamente se a quantidade coletada não coincidir.
- Garantir que o resultado bem-sucedido da data corrente via `GetList` seja cacheado com TTL e reutilizado nas próximas consultas.
- Alinhar a CLI à mesma seleção de fonte da GUI, preservando o formato de saída atual.

#### Fixed

- Corrigir o parser CSV para `splitlines()` e `strip()` por campo, removendo `\r`, ignorando linhas vazias e rejeitando linhas malformadas.
- Não cachear resultados vazios ou parciais; resultados vazios/parciais já gravados passam a ser tratados como cache miss e são descartados.
- Proteger os gráficos e o view-model contra listas vazias: exibir estado vazio informativo em vez de lançar `ValueError` ou deixar a área em branco.

### [refactor-clean-architecture-headless-tests](openspec/changes/archive/2026-10-19-refactor-clean-architecture-headless-tests/) Os guardrails de arquitetura vão bloquear novas violações, mas as dívidas atuais continuam impedindo testes verdadeiramente headless e a reutilização de regras pela futura CLI.

#### Changed

- Mover regras de negócio hoje embutidas na GUI para a camada de aplicação: data útil mais próxima, validação de data de consulta (futura/antiga), janela de histórico e estatísticas de taxas.
- Extrair a seleção de payload de exportação (bruto, consolidado, evolução) e o estado de habilitação de controles para um view-model/controlador headless, sem importar Tkinter.
- Mover transformações puras de dados de gráfico (`_nearest_ticks`, interpolações, grades 3D) de `presentation/charts.py` para a camada de aplicação.
- Expor `montar_evolucao_resumo` pela API pública de `application.analyze`, eliminando imports de módulos privados pela GUI.
- Reorganizar a CLI como composition root que instancia adapters e chama casos de uso, preparando a implementação futura de comandos por parâmetro sem duplicar regras da GUI.
- Migrar para testes headless os testes de UI que validam regras, exportação, dispatch de gráficos e estado de controles, mantendo em UI apenas testes de montagem/apresentação de widgets.
- Reduzir o UI test budget após a migração e remover as aprovações de arquitetura que deixarem de ser necessárias.

#### Removed

- Remover a dependência `application -> presentation`: configurações passam a ser construídas a partir de mappings/dados simples; `Settings` continua na presentation/infrastructure de composição.
- Remover `os` da camada `domain`, movendo o caminho do atalho para `infrastructure/desktop.py`.

### [set-first-run-defaults](openspec/changes/archive/2026-10-20-set-first-run-defaults/) Hoje a primeira execução em uma máquina sem `settings.json` abre a aplicação em "Curva curta", com evolução e painel de análise desligados.

#### Added

- Tratar a ausência do arquivo de settings como primeira execução e aplicar, nesse caso, os padrões `view_mode = "consolidated"`, `evolution = true` e `sidebar = true`.

#### Changed

- Manter "3D" desmarcado, a data padrão como hoje e a licença/comportamentos existentes inalterados.
- Preservar integralmente os settings já gravados: arquivos existentes continuam sendo carregados como estão, mesmo que não contenham alguma dessas chaves.
- Não alterar os defaults usados para arquivos existentes/corrompidos que não definam uma chave; esses continuam seguindo os padrões atuais.
- Ajustar a expectativa do painel de análise para que ele possa iniciar expandido na primeira execução, mantendo o comportamento recolhido nas execuções seguintes e no restante do ciclo de vida.

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.0.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
