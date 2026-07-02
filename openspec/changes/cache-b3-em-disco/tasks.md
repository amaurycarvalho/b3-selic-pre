## 1. DiskCache core module

- [ ] 1.1 Criar `src/b3_selic_pre/infrastructure/disk_cache.py` com a classe `DiskCache`
- [ ] 1.2 Implementar `_cache_path(date) -> Path` seguindo XGD_CACHE_HOME
- [ ] 1.3 Implementar `_read(date) -> list[RateRecord] | None` com envelope JSON (cached_at, ttl_minutes, records) e detecção de corrupção
- [ ] 1.4 Implementar `_write(date, records, ttl_minutes)` serializando envelope JSON
- [ ] 1.5 Implementar `_is_valid(cached_at, ttl_minutes) -> bool` (se ttl_minutes for 0 ou None, sempre válido; senão, checa idade)
- [ ] 1.6 Implementar `_housekeeping(max_age_days=365)` que lista arquivos no cache dir e remove os expirados

## 2. CachedB3Client class

- [ ] 2.1 Criar `src/b3_selic_pre/infrastructure/cached_client.py` com a classe `CachedB3Client`
- [ ] 2.2 `__init__(cache_dir=None, ttl_minutes=30, max_age_days=365)` — instancia `DiskCache`, aceita parâmetros opcionais
- [ ] 2.3 Implementar `fetch_reference_rates(date, force=False, **kwargs)` — verifica cache (se não force), chama `b3_client.fetch_reference_rates` em caso de miss, salva no cache, roda housekeeping
- [ ] 2.4 Implementar `fetch_rates_download(date, force=False)` — mesmo padrão, chamando `b3_client.fetch_rates_download`
- [ ] 2.5 Implementar `fetch_historical_rates(base_date, force=False, **kwargs)` — itera as 5 datas, verifica cache individual para cada uma; usa TTL de hoje só para a data atual

## 3. Integrar CLI

- [ ] 3.1 Em `src/b3_selic_pre/presentation/cli.py`: substituir `fetch_reference_rates(ref_date)` por `CachedB3Client().fetch_reference_rates(ref_date, force=args.no_cache)` se existir flag
- [ ] 3.2 Adicionar flag `--no-cache` ao argparse (opcional, para forçar refresh no CLI)

## 4. Integrar GUI

- [ ] 4.1 Em `src/b3_selic_pre/presentation/gui.py`: instanciar `CachedB3Client` como atributo de `SelicPreApp`
- [ ] 4.2 Substituir chamadas a `fetch_reference_rates`, `fetch_rates_download` e `fetch_historical_rates` pelo client cacheado
- [ ] 4.3 Garantir que o botão "Buscar" use `force=True` (sempre baixar da B3 quando o usuário clica explicitamente)
- [ ] 4.4 Garantir que a evolução histórica (`toggle_evolution`) use o cache (sem force) para evitar baixar tudo de novo

## 5. Testes

- [ ] 5.1 Testar `DiskCache._read` com cache hit (arquivo válido)
- [ ] 5.2 Testar `DiskCache._read` com cache miss (arquivo inexistente)
- [ ] 5.3 Testar `DiskCache._read` com JSON corrompido (deve deletar e retornar None)
- [ ] 5.4 Testar `DiskCache._is_valid` com/sem TTL, expirado, não expirado
- [ ] 5.5 Testar `DiskCache._housekeeping` remove arquivos antigos
- [ ] 5.6 Testar `CachedB3Client.fetch_reference_rates` com cache hit/miss
- [ ] 5.7 Testar `CachedB3Client.fetch_reference_rates` com `force=True` (ignora cache)
- [ ] 5.8 Testar `CachedB3Client.fetch_historical_rates` — cache granular por data
- [ ] 5.9 Testar integração CLI com `--no-cache`

## 6. Verificação final

- [ ] 6.1 Executar `pytest` e garantir que todos os testes existentes continuam passando
- [ ] 6.2 Executar linter (ruff) no código modificado
- [ ] 6.3 Verificar manualmente: abrir GUI, buscar data, fechar, reabrir — dados devem vir do cache
