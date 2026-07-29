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

## [0.9.1] - 2026-07-29

### [curva-curta-longa](openspec/changes/archive/2026-07-29-curva-curta-longa/) Renomeia rótulos da UI para "Curva curta" e "Curva longa"

#### Changed

- Título da janela: "B3 SELIC Pré v{version}" → "Taxas Referenciais SELIC (B3) v{version}"
- RadioButton "Detalhado" → "Curva curta" (modo raw)
- RadioButton "Consolidado" → "Curva longa" (modo consolidado)
- Títulos dos gráficos renomeados para "Curva Curta (SELIC Pré)" / "Curva Longa (SELIC Pré)" e variações de evolução
- Título 3D centralizado horizontalmente (removido deslocamento artificial)

#### Fixed

- pyproject.toml: versão corrigida de 0.8.0 → 0.9.1 (estava defasada)

[Unreleased]: https://github.com/amaurycarvalho/b3-selic-pre/compare/v0.9.1...HEAD
[0.9.1]: https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v0.9.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
