## Why

O `mutmut run` atual registrou 1.192 mutantes sobreviventes (de 3.338), uma taxa de sobrevivência alta que reduz a confiança no suite de testes e pressiona o score de mutação (hoje ~62%, abaixo do gate de 80% definido em `ci-quality-gate`). Muitos desses survivors são "matáveis" — falham por assertivas fracas ou entradas não cobertas — e podem ser eliminados apenas com testes adicionais, sem tocar em código de produção.

## What Changes

- Adicionar testes (novos casos em arquivos existentes ou novos arquivos) que matam os mutantes sobreviventes classificados como matáveis, agrupados por módulo.
- Pular e documentar os mutantes equivalentes (impossíveis de matar por qualquer input), registrando-os numa lista de exceção explícita.
- Manter invariantes de qualidade: `make lint` limpo e `make test` com cobertura >= 85%.
- **Não** executar `mutmut` em nenhuma etapa — a validação é feita rodando apenas o teste modificado/inserido.

## Capabilities

### New Capabilities

- `mutation-survivor-coverage`: define os requisitos para cobrir os mutantes sobreviventes matáveis com testes dedicados, e para documentar os mutantes equivalentes que serão ignorados.

### Modified Capabilities

<!-- Nenhuma mudança de requisito de produto. A qualidade de mutação é coberta por esta nova capability, não altera ci-quality-gate. -->

## Impact

- **Código de testes**: `tests/test_b3_selic_pre.py`, `tests/test_disk_cache.py`, `tests/test_evolucao_resumo.py`, `tests/test_novo_resumo.py`, e possivelmente novos arquivos em `tests/`.
- **Código de produção**: nenhuma alteração funcional; apenas eventuais anotações `# pragma: no mutate` caso o usuário opte por excluir mutantes equivalentes (a confirmar).
- **Dados de entrada**: `mutants/src/**/*.meta` (exit codes) e `mutants/src/**/*.py` (funções mutadas) são as fontes para identificar survivors sem rodar mutmut.
- **Ferramentas**: nenhuma dependência nova; usa pytest e ruff/flake8 já existentes.
