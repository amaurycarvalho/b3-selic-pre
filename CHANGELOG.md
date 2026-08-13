# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [rfc001-tesouro-direto-redesign](openspec/changes/rfc001-tesouro-direto-redesign/) Reprojetar extração de movimentações do Tesouro Direto seguindo Clean Architecture

#### Added

- Adicionar modelo de domínio `MovimentacaoTesouroDireto` como frozen dataclass
- Adicionar camada de cache seguindo o padrão `DiskCache` + `CachedClient` existente, com XDG paths
- Adicionar entry points na CLI e GUI para acesso aos dados do Tesouro Direto

#### Changed

- Reprojetar a feature de extração de movimentações do Tesouro Direto seguindo a Clean Architecture em 4 camadas (domain, application, infrastructure, presentation)
- Substituir scraping HTML pela API CKAN JSON nativa do portal Tesouro Transparente para obter metadados e URLs de recursos
- Eliminar dependências externas: usar `urllib` (não `requests`), CKAN API JSON (não `beautifulsoup4`), módulo `csv` nativo (não `pandas`)
- Atualizar o documento RFC-001 para refletir o design alinhado ao projeto

## [0.9.2] - 2026-08-13

### [gate-release-behind-ci](openspec/changes/archive/2026-08-12-gate-release-behind-ci/) O workflow de release atualmente constrói e publica binários sem nenhuma verificação de qualidade — lint, testes, complexidade, cobertura ou segurança.

#### Changed

- **ci.yml** passa a expor `workflow_call` e é refatorado em jobs separados (`lint`, `test`, `quality-gate`) conforme RFC-002 seção 4.1
- **release.yml** ganha um job `ci` que chama `ci.yml` via `workflow_call`, e o job `build` passa a depender de `ci` (`needs: ci`)
- **Makefile** é substituído pela versão da RFC-002 com todos os targets do quality gate (`quality-gate`, `complexity`, `duplication`, `mutation-check`, `security`, `install-quality-tools`, etc.)
- Nenhum binário é construído ou publicado sem o quality gate passar integralmente

### [kill-mutation-survivors](openspec/changes/archive/2026-08-13-kill-mutation-survivors/) O `mutmut run` atual registrou 1.192 mutantes sobreviventes (de 3.338), uma taxa de sobrevivência alta que reduz a confiança no suite de testes e pressiona o score de mutação.

#### Added

- Adicionar testes (novos casos em arquivos existentes ou novos arquivos) que matam os mutantes sobreviventes classificados como matáveis, agrupados por módulo
- Pular e documentar os mutantes equivalentes (impossíveis de matar por qualquer input), registrando-os numa lista de exceção explícita

#### Changed

- Manter invariantes de qualidade: `make lint` limpo e `make test` com cobertura >= 85%
- **Não** executar `mutmut` em nenhuma etapa — a validação é feita rodando apenas o teste modificado/inserido

### [speed-up-slow-gui-tests](openspec/changes/archive/2026-08-13-speed-up-slow-gui-tests/) `make test` (256 tests) leva ~51s, dos quais ~50s vêm de apenas 22 testes de GUI (`tests/test_b3_selic_pre_gui.py`).

#### Changed

- Reutilizar uma única instância de `tk.Tk` + `SelicPreApp` por classe de teste (`setUpClass`/`tearDownClass`), com reset de estado em `setUp`, em vez de reconstruir o app a cada teste
- Isolar os 3 testes de atalho desktop (que dependem do mock de `shortcut_exists` na construção) para reutilizar 2 apps compartilhados (um com atalho, um sem) em vez de criar um app novo por teste
- Introduzir um *seam* opcional na construção do app para permitir injetar um widget de data mais barato que `tkcalendar.DateEntry` nos testes
- Manter comportamento e cobertura de teste equivalentes; nenhuma mudança de funcionalidade de produto

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.9.2...HEAD
[0.9.2]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.9.2

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
