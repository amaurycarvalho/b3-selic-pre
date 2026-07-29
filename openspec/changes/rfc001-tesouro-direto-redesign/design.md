## Context

O RFC-001 propõe extrair dados de movimentações diárias do Tesouro Direto do portal Tesouro Transparente (CKAN). A proposta atual usa uma classe monolítica `ExtratorTesouroDireto` que mistura HTTP, parsing HTML, download de CSV e processamento de dados num único artefato, com dependências externas (`requests`, `beautifulsoup4`, `pandas`) não presentes no projeto.

O projeto `b3-selic-pre` segue Clean Architecture em 4 camadas (ADR-001), usa apenas `urllib` para HTTP, possui cache em disco com XDG paths, dependency injection via `opener` para testabilidade, e entry points CLI + GUI. O design precisa reestruturar a feature do RFC-001 para aderir a esses padrões, minimizando atrito com o ecossistema existente.

O portal Tesouro Transparente é baseado em CKAN, que expõe uma API REST JSON documentada (`/api/3/action/package_show`). Isso elimina a necessidade de scraping HTML e permite acesso programático confiável a metadados e URLs de recursos.

## Goals / Non-Goals

**Goals:**
- Reestruturar a feature em 4 camadas Clean Architecture: domain, application, infrastructure, presentation
- Usar a API CKAN JSON para descoberta de dataset (substitui scraping HTML)
- Usar `urllib` nativo para todas as requisições HTTP
- Usar `csv.Sniffer` + `csv.DictReader` nativos para parsing do CSV (substitui `pandas`)
- Implementar cache em disco com XDG paths, seguindo o padrão `DiskCache` existente
- Implementar `CachedTesouroClient` wrappando o client com lógica de cache
- Adicionar entry point CLI (`--tesouro` flag) com saída formatada
- Adicionar aba/painel na GUI para visualização das movimentações
- Atualizar o documento RFC-001 para refletir o design alinhado
- Manter testabilidade via `opener` injection e `FakeResponse`

**Non-Goals:**
- Cruzamento dos dados do Tesouro Direto com a curva SELIC (melhoria futura)
- Armazenamento em banco de dados (PostgreSQL/SQLite) -- arquivos locais bastam
- Visualização com matplotlib (gráficos de movimentação) -- v1 usa tabela/texto
- Análise textual/classificação dos dados (similar ao motor de análise existente)
- Automatização de execuções diárias (cron job) -- consulta sob demanda
- Suporte a outros datasets do Tesouro Transparente além de "Vendas do Tesouro Direto"

## Decisions

### 1. API CKAN JSON em vez de scraping HTML

**Decisão:** Usar `GET /api/3/action/package_show?id=vendas-do-tesouro-direto` para obter metadados e URLs de recursos.

**Alternativa rejeitada:** Parsing de HTML com BeautifulSoup (`bs4`). O scraping é frágil -- qualquer mudança no layout quebra. A API CKAN é estável, retorna JSON estruturado e não requer dependências extras.

**Racional:** A API CKAN fornece o `resource_id`, `package_id`, URL de download, e metadados completos num único request JSON. O parsing é trivial com `json.loads()`, já usado extensivamente no `b3_client.py`. Nenhuma dependência nova necessária.

### 2. Módulo `csv` nativo em vez de `pandas`

**Decisão:** Usar `csv.Sniffer` para detectar dialeto e `csv.DictReader` para leitura tipada.

**Alternativa rejeitada:** `pandas.read_csv()`. O `pandas` é uma dependência pesada (~30 MB) não presente no projeto. Para um CSV de ~7 MB com colunas simples, o módulo `csv` nativo é suficiente e evita aumentar o binário PyInstaller.

**Racional:** O `b3_client.py` já faz parsing manual de CSV em `fetch_rates_download()` com `split(';')`. O módulo `csv` nativo oferece detecção automática de separador, tratamento de quoting e leitura linha-a-linha com baixo consumo de memória.

### 3. Cache em disco com reuso do padrão DiskCache

**Decisão:** Criar um `TesouroCache` que segue a mesma interface do `DiskCache` existente (get/put/housekeeping), armazenando em `~/.cache/b3-selic-pre/tesouro/`.

**Alternativa rejeitada:** Estender o `DiskCache` existente para suportar múltiplos tipos de dados. Isso acoplaria o cache genérico a domínios específicos, violando o SRP. Melhor criar uma instância separada com o mesmo padrão.

**Racional:** O dataset é cumulativo (sempre o arquivo completo desde 2002), então:
- Cache key é a data de download (não há "cache por data de consulta" como na curva SELIC)
- TTL aplicável se quisermos re-baixar após N horas (ex: 6h, já que atualiza diariamente)
- Download condicional via `If-Modified-Since` / `ETag` para evitar baixar 7 MB desnecessariamente

Storage path: `$XDG_CACHE_HOME/b3-selic-pre/tesouro/vendastesourodireto.csv` + `vendastesourodireto.json` (metadados).

### 4. Modelo de domínio como frozen dataclass

**Decisão:** Definir `MovimentacaoTesouroDireto` com campos: `data`, `titulo`, `venda`, `resgate`, `saldo`, `vencimento`.

```python
@dataclass(frozen=True)
class MovimentacaoTesouroDireto:
    data: str          # YYYY-MM-DD
    titulo: str        # Nome do título
    venda: float       # Volume de vendas (R$)
    resgate: float     # Volume de resgates (R$)
    saldo: float       # Saldo (R$)
    vencimento: str    # YYYY-MM-DD
```

**Racional:** Segue o padrão de `RateRecord` (`domain/models.py`). Frozen garante imutabilidade. Dataclass fornece `__eq__`, `__repr__` e desestruturação gratuita. Valores monetários como `float` (precisão suficiente para agregações -- `Decimal` seria overengineering neste estágio).

### 5. Estrutura de arquivos na camada application

**Decisão:** Criar `application/tesouro/` como subpacote, espelhando `application/analyze/`.

```
application/tesouro/
├── __init__.py        # Re-exporta processar_csv()
├── _processamento.py  # Leitura, validação e estruturação do CSV
└── _formatting.py     # Formatação de saída (JSON, texto tabular)
```

**Racional:** A análise de curva SELIC já usa subpacote (`analyze/`) com módulos internos prefixados `_`. Isso mantém a API pública limpa (`application/tesouro/processar_csv`) enquanto isola implementação.

### 6. Entry points: CLI flag e aba na GUI

**Decisão:**
- **CLI:** Adicionar `--tesouro` como subcomando ao `argparse` existente
- **GUI:** Adicionar aba "Tesouro Direto" no `ttk.Notebook` com tabela scrollable (Treeview) e botão "Atualizar"

**Alternativa rejeitada:** Criar um executável separado (ex: `b3-tesouro-direto`). Isso duplicaria infraestrutura de build/distribuição e confundiria o usuário. Melhor integrar como feature adicional do mesmo aplicativo.

**Racional:** A GUI já tem padrão de abas (implícito na sidebar) e a CLI já tem estrutura de subcomandos. Adicionar uma aba ao Notebook existente é idiomático para Tkinter.

### 7. Testabilidade via opener injection

**Decisão:** As funções de infraestrutura (`fetch_metadados`, `fetch_csv`) recebem `opener=urllib.request.urlopen` como parâmetro, permitindo injeção de `FakeResponse` nos testes.

**Racional:** Padrão já usado em `b3_client.py:fetch_reference_rates_page()`. Sem dependência de bibliotecas de mock externas.

## Risks / Trade-offs

- **[CKAN API pode ser descontinuada ou mudar]** → Mitigação: A API CKAN é padrão internacional usado por centenas de portais de dados abertos. O Tesouro Nacional usa CKAN desde 2015. Fallback: se a API JSON falhar, tentar a URL HTML como último recurso e emitir warning.
- **[Schema do CSV pode divergir do esperado]** → Mitigação: `csv.Sniffer` detecta automaticamente o separador. Mapeamento de colunas por nome (case-insensitive) com fallback para colunas desconhecidas (ignoradas, não quebram). Log warning para colunas não reconhecidas.
- **[7 MB de download pode ser lento em conexões ruins]** → Mitigação: Download condicional via `ETag`/`If-Modified-Since`. Progress callback para GUI mostrar barra. Timeout de 60s.
- **[Feature pode aumentar binário PyInstaller se mal implementada]** → Mitigação: Nenhuma dependência nova. Uso de `urllib` e `csv` nativos. Estimativa de impacto: < 5 KB de código Python adicional.
- **[Duplicação parcial com `b3_client.py` em padrões HTTP]** → Trade-off aceito: cada fonte de dados tem suas peculiaridades (JSON paginado vs CSV simples, CKAN vs B3 API). Extrair um `HttpClient` genérico seria prematuro. Se surgir uma terceira fonte, aí sim abstrair.

## Open Questions

- **O CSV usa vírgula ou ponto-e-vírgula como separador?** O RFC assume vírgula, mas dados governamentais brasileiros frequentemente usam `;`. O `csv.Sniffer` resolve isso em runtime.
- **O encoding do CSV é UTF-8 ou Latin-1?** Testar ambos com fallback, como `b3_client.py` já faz (`utf-8` → `latin-1`).
- **A GUI deve ter gráfico de barras/linha das movimentações?** Decidido como Non-Goal para v1. Pode ser adicionado como melhoria futura.
- **O cache deve expirar?** Dataset atualiza diariamente com defasagem de D+2. TTL de 6h no CSV garante que o usuário veja dados frescos sem abusar do servidor do Tesouro.
