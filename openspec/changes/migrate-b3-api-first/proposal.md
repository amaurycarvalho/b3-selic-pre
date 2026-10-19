## Why

O cliente atual usa `urllib` e depende de `GetDownloadFile` (base64/CSV) para datas históricas. O spike mostrou que esse caminho é frágil: o parser deixa `\r` no campo `rate`, o download e a API retornam `200 OK` com corpo vazio de forma intermitente, e o código procura um `totalCount` que não existe na resposta real. A B3 já expõe uma API JSON direta (`GetList`) com metadados de página e uma API de disponibilidade (`GetDate`), usadas pelo próprio site da B3.

## What Changes

- Introduzir um transporte HTTP baseado em `requests`, com `Session` por thread, pooling, retries de conexão/429/5xx, timeout `(5, 20)` e budget de ~20–30 s no pior caso.
- Criar um cliente API-first para a B3 usando `GetProducts`, `GetDate` e `GetList`, com metadados `page.totalRecords`/`page.totalPages` e validação de completude.
- Adicionar retry de aplicação para respostas `200` vazias/incompletas (o retry HTTP não cobre isso) e classificar a falha persistente como `CommunicationError`.
- Usar `GetDate` como fonte de verdade da janela disponível (20 datas úteis no spike) e alinhar a validação de histórico da GUI/CLI e o modo evolução.
- Manter `GetDownloadFile`/CSV apenas como fallback temporário para datas fora da janela da API; corrigir o parser para `splitlines()`/`strip()`.
- Adicionar as chaves `http_ca_bundle`, `http_proxy`, `https_proxy` e `no_proxy` ao `settings.json`, com validação e defaults seguros; manter a verificação TLS sempre ativa.
- Adicionar `requests` às dependências de runtime e validar o build PyInstaller (certifi/charset_normalizer).
- Atualizar ADR/CHANGELOG/RFC-001 para substituir a decisão “usar `urllib`, não `requests`”.
- **BREAKING** para datas fora da janela `GetDate` e sem dados no fallback CSV: o comportamento de histórico deixa de ser “qualquer data” e passa a ser explícito sobre a janela disponível.

## Capabilities

### New Capabilities

- `b3-api-client`: transporte HTTP, endpoints `GetProducts`/`GetDate`/`GetList`, paginação, retries/validação, contrato de erros e fallback CSV temporário.

### Modified Capabilities

- `curve-evolution`: a busca de múltiplas datas deixa de ser baseada em `GetDownloadFile` e passa a usar `GetList`/`GetDate`, com fallback CSV para datas fora da janela.
- `desktop-rate-browser`: a GUI usa a API como fonte primária, valida a janela disponível via `GetDate` e trata a indisponibilidade de datas.
- `persistence`: adiciona as chaves de configuração de TLS/proxy do cliente HTTP.

## Impact

- Novos módulos: `infrastructure/http_client.py` e `infrastructure/b3_api.py` (ou equivalente), além de ajustes em `b3_client.py`/`cached_client.py`.
- Alterações em `presentation/settings.py`, `presentation/gui/fetch.py`, `presentation/gui/launch.py`, `presentation/cli.py` e nos composition roots.
- Nova dependência de runtime `requests` (`urllib3`, `certifi`, `charset_normalizer`, `idna`) e impacto no binário PyInstaller.
- Atualização de testes headless de HTTP, paginação, retries, settings, cache, CLI e GUI; smoke test real contra a B3.
- O CSV permanece como fallback temporário; sua remoção definitiva é um follow-up depois que a janela da API for validada em produção.
- A mudança de logging já entregue (`add-application-logging`) continua sendo o contrato de `CommunicationError`: rede/HTTP e resposta incompleta persistente em uma linha; JSON/schema inválido com traceback.
