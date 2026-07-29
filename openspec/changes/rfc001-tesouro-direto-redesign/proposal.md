## Why

O RFC-001 (Movimentações do Tesouro Direto) define uma feature futura para extrair dados de vendas de títulos públicos do portal Tesouro Transparente, mas sua proposta atual viola a arquitetura Clean Architecture do projeto (ADR-001), introduz dependências externas não aprovadas (`requests`, `beautifulsoup4`, `pandas`), não segue os padrões de cache e XDG paths já estabelecidos, e não define integração com a presentation layer (CLI/GUI). É necessário reprojetar o RFC para aderir ao projeto antes que a feature possa ser implementada.

## What Changes

- Reprojetar a feature de extração de movimentações do Tesouro Direto seguindo a Clean Architecture em 4 camadas (domain, application, infrastructure, presentation)
- Substituir scraping HTML pela API CKAN JSON nativa do portal Tesouro Transparente para obter metadados e URLs de recursos
- Eliminar dependências externas: usar `urllib` (não `requests`), CKAN API JSON (não `beautifulsoup4`), módulo `csv` nativo (não `pandas`)
- Adicionar modelo de domínio `MovimentacaoTesouroDireto` como frozen dataclass
- Adicionar camada de cache seguindo o padrão `DiskCache` + `CachedClient` existente, com XDG paths
- Adicionar entry points na CLI e GUI para acesso aos dados do Tesouro Direto
- Atualizar o documento RFC-001 para refletir o design alinhado ao projeto

## Capabilities

### New Capabilities
- `tesouro-direto-domain`: Modelo de domínio (frozen dataclass) para registros de movimentação do Tesouro Direto
- `tesouro-direto-infrastructure`: Cliente HTTP via CKAN API + download de CSV + cache em disco com XDG paths
- `tesouro-direto-processing`: Processamento, validação e estruturação dos dados extraídos do CSV
- `tesouro-direto-presentation`: Entry points CLI e GUI para consulta e visualização das movimentações

### Modified Capabilities
<!-- Nenhum spec existente sofre alteração de requisito com esta mudança -->
<!-- Reuso de disk-cache, persistence e data-export é detail de implementação, não de spec -->

## Impact

- Novos arquivos em `src/b3_selic_pre/domain/`, `application/tesouro/`, `infrastructure/` e `presentation/`
- Nenhuma dependência externa nova adicionada ao `pyproject.toml`
- RFC-001 atualizado em `docs/rfcs/` para refletir o design alinhado
- PRD (`docs/PRD.md`) atualizado para refletir a inclusão da feature no escopo
- Nenhuma breaking change em código existente -- a feature é aditiva
