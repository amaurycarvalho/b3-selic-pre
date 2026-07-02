## Why

O aplicativo baixa dados da B3 toda vez que o usuário consulta uma data ou ativa a evolução histórica. Se o usuário consulta a mesma data repetidamente (ex: alternando entre modo detalhado e consolidado, ou fechando e reabrindo o app), os mesmos dados são baixados de novo — desperdiçando rede e tempo. Um cache em disco elimina essas requisições redundantes.

## What Changes

- Criar sistema de cache em disco para dados baixados da B3, chaveado por data
- Ao buscar taxas, verificar cache antes de fazer requisição HTTP
- Cache granular: cada data tem seu próprio arquivo JSON
- TTL de 30 minutos apenas para a data atual; datas passadas são imutáveis
- Corrupção de JSON tratada como cache miss (deleta + refetch)
- Housekeeping automático: limpa caches com mais de 1 ano (parametrizável)
- Usar diretório XDG_CACHE_HOME (`~/.cache/b3-selic-pre/rates/`)
- Nenhuma mudança visual na UI — o cache é transparente

## Capabilities

### New Capabilities
- `disk-cache`: Cache em disco para respostas da API B3, com suporte a TTL, detecção de corrupção e housekeeping automático

### Modified Capabilities
<!-- Nenhuma — é uma capability nova, sem mudanças nas existentes -->

## Impact

- `src/b3_selic_pre/infrastructure/b3_client.py`: Adicionar verificação de cache nas funções de fetch
- `src/b3_selic_pre/infrastructure/`: Novo módulo `disk_cache.py` com a classe `CachedB3Client` e lógica de cache
- `src/b3_selic_pre/presentation/cli.py`: Usar `CachedB3Client` em vez de chamar `fetch_reference_rates` diretamente
- `src/b3_selic_pre/presentation/gui.py`: Usar `CachedB3Client` em vez de chamar funções de fetch diretamente
- Nenhuma dependência nova adicionada (apenas módulos stdlib: `json`, `os`, `pathlib`, `datetime`)
