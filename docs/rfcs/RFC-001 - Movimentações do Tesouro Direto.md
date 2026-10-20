# RFC-001 - Movimentações do Tesouro Direto

**Status:** preliminar — bloqueada por spike de descoberta
**Última revisão:** 2026-10-20

---

## 1. Status e pré-requisito bloqueante

Este RFC foi reestruturado para refletir as decisões atuais do projeto. Ele é uma **versão preliminar**: o schema real do CSV do Tesouro Transparente nunca foi verificado neste repositório e o próprio RFC original reconhece que a estrutura das colunas deve ser confirmada após o download.

Antes de qualquer implementação, é obrigatório um spike de descoberta que confirme:

1. o endpoint CKAN correto e o identificador/nome real do dataset;
2. as colunas reais do CSV, com nomes, acentos, tipos e obrigatoriedade;
3. se o dataset contém apenas vendas ou também resgates/saldo;
4. encoding, BOM, delimitador, tamanho, periodicidade e defasagem;
5. suporte a `ETag`, `Last-Modified` e `304 Not Modified`.

Enquanto o spike não for concluído:

- o modelo de domínio é provisório;
- as colunas, filtros e agregações são provisórios;
- a change não pode ser implementada;
- este RFC, as specs e as tarefas devem ser revisados com o schema verificado.

---

## 2. Objetivo

Disponibilizar, para a CLI e para a GUI do `b3-selic-pre`, uma consulta às movimentações do Tesouro Direto publicadas no portal Tesouro Transparente, com:

- descoberta do dataset via API CKAN JSON;
- download e cache local do CSV cumulativo;
- processamento e validação com a biblioteca padrão;
- filtros por título e período;
- saída CSV/JSON na CLI;
- janela separada na GUI.

A feature é aditiva e não altera a consulta da curva SELIC Pré.

---

## 3. Decisões de arquitetura

### 3.1 Clean Architecture

A feature segue as quatro camadas do projeto:

| Camada | Responsabilidade |
| --- | --- |
| `domain` | Modelo de registro e constantes puras |
| `application` | Parsing, validação, filtros, agregação e formatação |
| `infrastructure` | Cliente CKAN, download do CSV, cache e metadados |
| `presentation` | CLI (`tesouro`) e janela da GUI |

As guardas de `tests/test_architecture.py` continuam válidas: `domain` é puro; `application` não importa UI, rede ou `presentation`; `infrastructure` não importa UI.

### 3.2 Dependências

Nenhuma dependência externa nova. Usar apenas:

- `urllib` para HTTP;
- `csv` para parsing;
- `json` para metadados;
- `zipfile`/`io`/`hashlib` se o spike revelar necessidade.

`requests`, `BeautifulSoup` e `pandas` estão descartados.

---

## 4. Fonte de dados

### 4.1 Descoberta via CKAN

A descoberta usa a API CKAN JSON:

```text
GET https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show?id=<dataset>
```

A resposta fornece metadados e a lista de recursos. O sistema extrai a URL do recurso CSV. O PDF de metadados não é consumido nesta change e não é extraído.

### 4.2 Download

O download usa `urllib.request` com:

- leitura em chunks;
- timeout padrão de 60 segundos;
- retry com backoff/jitter para corpo vazio, reutilizando o padrão de `infrastructure/b3_retry.py`;
- `ETag` e `If-Modified-Since` quando disponíveis;
- tratamento explícito de `304 Not Modified` para reutilizar o cache.

Falhas de rede, HTTP, timeout e corpo vazio após os retries são `CommunicationError`.

### 4.3 Dataset cumulativo

O dataset é cumulativo desde 2002 e atualizado diariamente com defasagem. Portanto:

- há apenas um CSV local, não um arquivo por data;
- não há housekeeping de arquivos datados;
- a atualização substitui a versão anterior de forma atômica.

---

## 5. Cache

### 5.1 Localização

```text
$XDG_CACHE_HOME/b3-selic-pre/tesouro/
├── vendastesourodireto.csv
└── metadata.json
```

No Linux, `$XDG_CACHE_HOME` tem fallback para `~/.cache`. O caminho é resolvido por `infrastructure/xdg.py`.

### 5.2 Regras

- TTL de 6 horas.
- Download para arquivo temporário, validação e substituição atômica via `cache_payload.write_atomic`.
- Se o download falhar, a versão válida anterior é preservada.
- Cache ausente, vencido, vazio, corrompido ou incompleto é tratado como miss.
- Leitura somente leitura não remove, renomeia nem altera arquivos.
- Metadados incluem `ETag`, `Last-Modified`, instante do download e informações do dataset.

---

## 6. Processamento

### 6.1 Modelo provisório

A versão preliminar define um frozen dataclass `RegistroTesouroDireto` com:

| Campo | Tipo provisório |
| --- | --- |
| `data` | `str` ISO `AAAA-MM-DD` |
| `titulo` | `str` |
| `venda` | `float` |
| `resgate` | `float` |
| `saldo` | `float` |
| `vencimento` | `str` ISO `AAAA-MM-DD` |

O spike pode renomear o modelo para `VendaTesouroDireto` e ajustar os campos se o dataset for apenas de vendas.

### 6.2 Parsing

- Tentar UTF-8 com BOM, UTF-8 e Latin-1, nessa ordem.
- Validar o delimitador (`;` ou `,`).
- Mapear colunas sem distinção de caixa/acentos.
- Exigir as colunas obrigatórias confirmadas pelo spike.
- Ignorar colunas desconhecidas com aviso.
- Converter tipos e reportar linha/coluna em erros.
- CSV vazio ou sem registros gera erro de dados e não é cacheado.

### 6.3 Filtros e agregação

- `filtrar_por_titulo`: parcial, sem caixa/acentos.
- `filtrar_por_periodo`: intervalo inclusivo.
- `agregar_por_titulo`: totais de venda, resgate e saldo.

### 6.4 Formatação

- CSV: delimitador `;`, decimal `.`, cabeçalho conforme o schema.
- JSON: `fonte`, `data_extracao`, `total_registros`, `periodo` e `registros`.
- A camada `application` devolve texto/dict; a presentation serializa JSON.

---

## 7. CLI

### 7.1 Subcomando

```text
b3-selic-pre tesouro [--titulo T] [--inicio AAAA-MM-DD] [--fim AAAA-MM-DD]
                     [--json] [--no-cache]
```

- Sem `--json`: CSV no stdout.
- Com `--json`: payload estruturado.
- `--no-cache`: força download.
- `--titulo`: filtro parcial e sem caixa/acentos.
- `--inicio`/`--fim`: período inclusivo.

### 7.2 Códigos de retorno

| Código | Significado |
| --- | --- |
| `0` | Sucesso |
| `1` | Falha de comunicação ou de dados |
| `2` | Erro de uso ou validação |

Nenhuma flag no nível raiz. `b3-selic-pre --tesouro` é inválido e retorna `2`.

### 7.3 Integração

O subcomando é adicionado em `presentation/cli_parser.py` e implementado em `presentation/cli_commands.py`; o cliente é montado no composition root em `presentation/cli.py`.

---

## 8. GUI

### 8.1 Janela separada

A GUI ganha um botão "Tesouro Direto" na barra superior. O botão abre uma janela `Toplevel` independente, com:

- tabela `ttk.Treeview` rolável;
- filtro por título;
- datas inicial/final;
- ação "Atualizar" (reutiliza cache) e opção "Ignorar cache";
- progresso e status próprio.

A janela principal, o gráfico, o sidebar, o statusbar e o escudo de inicialização permanecem inalterados.

### 8.2 Threading e view-model

O download roda em thread e a UI é atualizada via `root.after`. O estado da janela (linhas, filtros, controles e status) é calculado por um view-model headless em `presentation/tesouro_view_model.py`.

### 8.3 Testes de UI

Testes que importam Tkinter ou a GUI são marcados com `@pytest.mark.ui` e respeitam o orçamento atual de 5 testes. A preferência é testar o view-model headless.

---

## 9. Erros e logging

- `CommunicationError` para rede, HTTP, timeout e corpo vazio após retries.
- Erro de dados para CSV malformado, colunas ausentes e valores inválidos.
- Falhas de comunicação em uma linha de log, sem traceback.
- Exceções inesperadas com traceback completo.
- CLI em `stderr` com código `1`/`2`; GUI mostra a mensagem e permanece utilizável.

---

## 10. Testes e qualidade

- Testes headless de cliente, cache, parsing, filtros, agregação e formatação.
- Testes de UI apenas para montagem/wiring.
- `make lint`, `make complexity` e suíte completa, por envolver `domain`, CLI, GUI e cache.
- Teste manual opcional da CLI e da janela.

---

## 11. Non-goals

- Tools MCP para Tesouro.
- Exportação Tesouro no `exportar` ou botão de cópia dedicado.
- Gráficos de movimentação.
- Banco de dados.
- Agendamento/cron.
- Cruzamento com a curva SELIC.
- Atualização do PRD antes do spike e da aprovação de implementação.
- Outros datasets do Tesouro Transparente.

---

## 12. Checklist do spike

- [ ] Confirmar endpoint e identificador do dataset.
- [ ] Baixar amostra do CSV e registrar tamanho, encoding, BOM e delimitador.
- [ ] Registrar cabeçalho e tipos reais.
- [ ] Confirmar se há vendas, resgates e saldo.
- [ ] Confirmar `ETag`/`Last-Modified`/304.
- [ ] Confirmar periodicidade e defasagem.
- [ ] Atualizar este RFC, as specs e as tarefas com o schema verificado.

---

## 13. Referências

- `docs/adrs/ADR-001.md` — Clean Architecture.
- `openspec/specs/architecture-governance/spec.md`.
- `openspec/specs/cli-interface/spec.md`.
- `openspec/specs/disk-cache/spec.md`.
- `openspec/specs/application-logging/spec.md`.
- `openspec/specs/test-suite-performance/spec.md`.
