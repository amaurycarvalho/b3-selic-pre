## Why

A CLI atual concentra data, visão, GUI, atalho, cache e versão em flags planas e não oferece caminhos para atualizar a evolução da curva, gerar o texto determinístico de análise ou exportar esses artefatos. Também não registra uma linha por invocação, o que dificulta auditoria e diagnóstico de uso.

## What Changes

- **BREAKING** Reorganizar a CLI em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `gui` e `criar-atalho`.
- **BREAKING** Remover a sintaxe antiga baseada em data posicional e flags `--today`, `--yearly`, `--gui`, `--create-shortcut`, `--no-cache` no nível raiz.
- **BREAKING** Substituir `--visao` e `--evolucao` por um único `--curva curta|longa|ambas`.
- Manter `b3-selic-pre` sem argumentos abrindo a GUI; `gui` passa a ser o subcomando explícito equivalente.
- Adicionar `atualizar --data AAAA-MM-DD` (default: hoje), que carrega a curva de referência e a janela de evolução, gera o texto executivo e o texto de evolução da curva.
- Adicionar `exportar` com seleção de conteúdo: evolução curta, evolução longa, análise determinística e log atual da aplicação, com saída em stdout (um artefato) ou diretório (vários artefatos).
- Registrar uma linha por invocação da CLI com comando, argumentos, início, fim, duração e código de saída, reutilizando formato e rotação diária do log da aplicação.
- Documentar os parâmetros em `docs/misc/cli.md` e adicionar uma seção resumida apontando para esse arquivo no `README.md`.
- Atualizar manifestos de atalho e referências de spec que ainda usam `--gui` ou `--create-shortcut`.

## Capabilities

### New Capabilities
- `cli-interface`: subcomandos de verbo, parâmetros comuns, semântica de `--curva`, defaults de data, regras de saída e códigos de retorno da CLI.

### Modified Capabilities
- `application-logging`: nova exigência de registro de invocação da CLI com metadados de execução e código de saída.
- `headless-application-services`: a CLI passa a montar serviços headless compartilhados para análise, evolução e exportação detalhada, sem duplicar regras.
- `shortcut-installer`: criação de atalho passa a usar `criar-atalho`; a GUI é referenciada por `gui`.
- `desktop-entry`: o campo `Exec` do `.desktop` passa a usar `gui` e o caminho programático de criação usa `criar-atalho`.
- `yearly-consolidation`: a consolidação anual deixa de usar `--yearly` e passa a ser `consultar --curva longa`.
- `app-icon`: cenários de lançamento e criação de atalho passam a citar `gui` e `criar-atalho` em vez das flags antigas.

## Impact

- Reescrita de `src/b3_selic_pre/presentation/cli.py` com subparsers e composition root.
- Novos formatadores/serviços em `application` para CSV detalhado da evolução e textos de análise.
- Ajustes em `src/b3_selic_pre/presentation/gui/launch.py` para não reconfigurar o log já iniciado pela CLI.
- Ajustes em `src/b3_selic_pre/infrastructure/desktop.py` e `b3-selic-pre.desktop`.
- Reescrita de `tests/test_cli.py` e ajustes em testes de atalho/desktop; novos testes headless para exportação e análise.
- Novo `docs/misc/cli.md` e seção de linha de comando no `README.md`.
- Sem novas dependências externas.
