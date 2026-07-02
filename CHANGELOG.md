# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2026-07-02

### [cache-b3-em-disco](openspec/changes/archive/2026-07-02-cache-b3-em-disco/) Cache em disco para evitar downloads redundantes da B3

#### Added

- Criar sistema de cache em disco para dados baixados da B3, chaveado por data (granular: 1 arquivo JSON por data)
- Verificar cache antes de fazer requisição HTTP; cache hit retorna dados sem chamar a B3
- TTL de 30 minutos apenas para a data atual; datas passadas são imutáveis (sem expiração)
- Corrupção de JSON tratada como cache miss (deleta arquivo + refetch automático)
- Housekeeping automático: limpa caches com mais de 1 ano (parametrizável via `max_age_days`)
- Cache segue XDG: `~/.cache/b3-selic-pre/rates/` no Linux
- Classe `CachedB3Client` encapsula fetch + cache, usada por CLI e GUI
- Indicador visual na barra de status da GUI: mostra "Cache" vs "API B3" / "Arquivo oficial B3"
- Flag `--no-cache` no CLI para forçar download fresco ignorando o cache

### [evolucao-resumo-executivo](openspec/changes/archive/2026-07-02-evolucao-resumo-executivo/) Adiciona painel de evolução da curva ao sidebar da GUI

#### Added

- Adiciona a seção "Resumo Executivo — Evolução da Curva" ao sidebar da GUI, abaixo do painel de Curva Atual
- Adiciona 2 novos arquivos ao módulo `application/analyze/`: `_evolucao.py` e `_texto_evolucao.py`
- Adiciona parâmetros de configuração no `settings.json` sob a chave `curva_evolucao`
- Adiciona o sub-painel "Evolução da Curva" no sidebar da GUI, visível apenas quando o modo Evolução está ativo
- Adiciona a struct `EvolutionReport` com os indicadores calculados e texto gerado

#### Changed

- Atualiza `__init__.py` do módulo `analyze` para exportar a nova função `analyze_evolution()`

### [novo-resumo-executivo](openspec/changes/archive/2026-07-02-novo-resumo-executivo/) Substitui motor de análise por Resumo Executivo da Curva de Juros

#### Added

- Cria 4 novos arquivos no módulo `application/analyze/`: `__init__.py`, `_resumo.py`, `_texto.py`, `_config.py`
- Adiciona novos parâmetros de configuração no `settings.json` sob as chaves `curva_juros` e `curva_evolucao`

#### Changed

- **BREAKING**: Substitui completamente o módulo `application/analyze/` por nova implementação baseada no Resumo Executivo da Curva de Juros
- Atualiza o sidebar da GUI para exibir o novo layout do Resumo Executivo (tags tk.Text header/positive/negative, 7 blocos nomeados + mensagem final)
- **BREAKING**: Altera o contrato da função `analyze()` — agora recebe parâmetros de configuração adicionais e retorna `AnalysisReport` com estrutura diferente

#### Removed

- Remove 8 arquivos do motor antigo (`_metrics.py`, `_features.py`, `_classifier.py`, `_registry.py`, `_scoring.py`, `_templates.py`, `_report.py`, `_metrics_evolution.py`)
- Remove a classe de análise para os modos "consolidado" e "evolução" (placeholders)
- Remove todos os testes antigos do motor de análise (`test_analyze.py`)

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.9.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
