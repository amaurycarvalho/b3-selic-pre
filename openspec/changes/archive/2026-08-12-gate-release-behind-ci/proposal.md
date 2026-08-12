## Why

O workflow de release atualmente constrói e publica binários sem nenhuma verificação de qualidade — lint, testes, complexidade, cobertura ou segurança. Isso significa que código com qualidade degradada pode chegar ao usuário final sem barreira alguma. A RFC-002 já definiu o quality gate completo, mas o `release.yml` ainda não o executa antes do build.

## What Changes

- **ci.yml** passa a expor `workflow_call` e é refatorado em jobs separados (`lint`, `test`, `quality-gate`) conforme RFC-002 seção 4.1
- **release.yml** ganha um job `ci` que chama `ci.yml` via `workflow_call`, e o job `build` passa a depender de `ci` (`needs: ci`)
- **Makefile** é substituído pela versão da RFC-002 com todos os targets do quality gate (`quality-gate`, `complexity`, `duplication`, `mutation-check`, `security`, `install-quality-tools`, etc.)
- Nenhum binário é construído ou publicado sem o quality gate passar integralmente

## Capabilities

### New Capabilities
- `ci-quality-gate`: Pipeline de CI reutilizável com jobs sequenciais de lint, teste e quality gate (complexidade, duplicação, cobertura, mutação, segurança), executável tanto por push/PR quanto por `workflow_call` a partir do release

### Modified Capabilities
- `release-automation`: O workflow de release agora exige que o quality gate do CI passe antes do build — novo job `ci` com `workflow_call`, `build` depende de `ci`

## Impact

- `.github/workflows/ci.yml` — refatorado para jobs separados com `workflow_call`
- `.github/workflows/release.yml` — novo job `ci`, `build` agora com `needs: ci`
- `Makefile` — substituído pela versão completa da RFC-002 com todos os targets de qualidade
- `docs/adrs/ADR-002.md` — novo ADR documentando a decisão de gatear releases atrás do CI
- Releases que falharem o quality gate não produzirão binários
