## Context

O aplicativo atualmente baixa dados da B3 em duas situações:

1. **Consulta avulsa** (`fetch_reference_rates` / `fetch_rates_download`): disparada pelo CLI (`main()`) ou GUI (`fetch_rates()`)
2. **Evolução histórica** (`fetch_historical_rates`): disparada pela GUI ao ativar "Evolução da curva", baixando 5 datas simultaneamente com `ThreadPoolExecutor`

Ambas são chamadas diretamente como funções do módulo `b3_client.py`. Não há cache entre chamadas — cada execução gera requisições HTTP para a B3.

O módulo `presentation/settings.py` já estabelece o padrão XDG para diretórios de configuração. O mesmo padrão será seguido para cache (`XDG_CACHE_HOME`).

## Goals / Non-Goals

**Goals:**
- Criar um `CachedB3Client` que encapsule fetch + cache em disco
- Cache granular por data (1 arquivo JSON por data)
- TTL de 30 minutos apenas para a data atual
- JSON corrompido → deletar arquivo e tratar como cache miss
- Housekeeping automático: limpar caches com mais de 1 ano (parametrizável por Config)
- Cache compartilhado entre CLI e GUI (mesmo diretório)

**Non-Goals:**
- Cache em memória LRU para a sessão atual
- Cache de outros recursos (icones, configurações)
- Invalidacão manual pelo usuário (o refresh via botão Buscar já força nova requisição)
- Compressão dos arquivos de cache (JSON é pequeno o suficiente)

## Decisions

### Decisão 1: Cache granular por data (Estratégia A)

Cada data tem seu próprio arquivo `~/.cache/b3-selic-pre/rates/2026-07-02.json`.

**Por que não cache atômico (bloco de 5 datas)?** O cache granular permite reaproveitamento: se o usuário consultar uma data avulsa no CLI que já foi baixada como parte do histórico, o cache já está populado. Também evita refetch de todas as 5 datas se apenas 1 expirar.

### Decisão 2: `CachedB3Client` como classe

Optou-se por uma classe em vez de decorator porque:
- Diferentes datas têm diferentes regras de TTL (só hoje tem TTL)
- O `fetch_historical_rates` precisa verificar cache data a data
- Fica mais fácil de testar com injeção de dependência

```python
class CachedB3Client:
    def __init__(self, cache_dir: str | None = None, ttl_minutes: int = 30):
        ...
    
    def fetch_reference_rates(self, date: str, **kwargs) -> list[RateRecord]:
        # Tenta cache → se miss, chama b3_client.fetch_reference_rates
    
    def fetch_rates_download(self, date: str) -> list[RateRecord]:
        # Tenta cache → se miss, chama b3_client.fetch_rates_download
    
    def fetch_historical_rates(self, base_date: str, **kwargs) -> dict[str, list[RateRecord]]:
        # Itera as 5 datas, verifica cache individual para cada uma
    
    def _housekeeping(self):
        # Remove caches com mais de max_age_days (default 365)
```

### Decisão 3: Formato JSON com envelope

```json
{
  "cached_at": "2026-07-02T09:00:00",
  "ttl_minutes": 30,
  "source": "download",
  "records": [
    {"day252": 1, "day360": 1, "rate": "14,65"}
  ]
}
```

**Por que não pickle?** JSON é legível, debugável, e não adiciona dependências. Pickle é mais rápido mas opaco e inseguro para leitura.

### Decisão 4: TTL de 30 min apenas para hoje

- Datas passadas são imutáveis na B3 → sem TTL, cache válido para sempre
- Hoje pode ser atualizado intraday → TTL de 30 min (configurável)
- Se TTL expirou ou JSON está corrompido → deleta arquivo, trata como miss

### Decisão 5: Housekeeping durante a carga

A limpeza de caches antigos roda como parte do processo de carga (após fetch bem-sucedido), não como background task.

- Critério: `now - data do cache > max_age_days` (default 365, configurável)
- Verifica todos os arquivos no diretório de cache
- Remove arquivos expirados silenciosamente

```python
def _housekeeping(self, max_age_days=365):
    cutoff = date.today() - timedelta(days=max_age_days)
    for f in Path(self.cache_dir).glob("*.json"):
        date_str = f.stem  # "2026-07-02"
        try:
            if date.fromisoformat(date_str) < cutoff:
                f.unlink()
        except ValueError:
            pass  # arquivo com nome inválido, ignora
```

### Decisão 6: Forçar refresh

O botão "Buscar" na GUI e a chamada no CLI devem ignorar o cache. O `CachedB3Client` terá um parâmetro `force=False` que, quando True, pula a verificação de cache.

### Decisão 7: Diretório de cache

| Sistema | Caminho |
|---------|---------|
| Linux   | `$XDG_CACHE_HOME/b3-selic-pre/rates/` (fallback: `~/.cache/b3-selic-pre/rates/`) |
| Windows | `%LOCALAPPDATA%/b3-selic-pre/cache/rates/` |
| macOS   | `~/Library/Caches/b3-selic-pre/rates/` |

Segue o mesmo padrão do `Settings` (`_xdg_path`).

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| B3 atualizar dados de datas passadas (improvável) | Sem TTL para passado → se ocorrer, usar force refresh |
| Cache ocupar espaço em disco | Housekeeping automático limpa dados > 1 ano; JSON é pequeno (~50KB por data) |
| Race condition: CLI e GUI lendo/escrevendo mesmo arquivo | Operações de leitura/escrita são atônicas em JSON pequeno; risco baixo |
| Data futura no cache | O cache só é populado com datas válidas; datas futuras não são consultadas |
| Timezone no `cached_at` | Usar UTC para evitar ambiguidade |
