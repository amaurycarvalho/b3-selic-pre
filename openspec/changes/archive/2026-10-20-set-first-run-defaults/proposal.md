## Why

Hoje a primeira execução em uma máquina sem `settings.json` abre a aplicação em "Curva curta", com evolução e painel de análise desligados. Esse estado inicial não destaca os recursos analíticos que a aplicação oferece e exige que o usuário reconfigure manualmente a visualização todas as vezes em que roda o produto pela primeira vez.

## What Changes

- Tratar a ausência do arquivo de settings como primeira execução e aplicar, nesse caso, os padrões:
  - "Curva longa" selecionada (`view_mode = "consolidated"`);
  - "Evolução da curva" marcada (`evolution = true`);
  - "Análise" marcada (`sidebar = true`).
- Manter "3D" desmarcado, a data padrão como hoje e a licença/comportamentos existentes inalterados.
- Preservar integralmente os settings já gravados: arquivos existentes continuam sendo carregados como estão, mesmo que não contenham alguma dessas chaves.
- Não alterar os defaults usados para arquivos existentes/corrompidos que não definam uma chave; esses continuam seguindo os padrões atuais.
- Ajustar a expectativa do painel de análise para que ele possa iniciar expandido na primeira execução, mantendo o comportamento recolhido nas execuções seguintes e no restante do ciclo de vida.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capacidade; o comportamento pertence a capacidades existentes. -->

### Modified Capabilities

- `persistence`: a ausência do arquivo de settings passa a usar um conjunto de defaults de primeira execução (`consolidated`, evolução ligada, análise ligada), preservando os defaults antigos para arquivos existentes e corrompidos.
- `auto-analysis`: o painel de análise pode iniciar expandido na primeira execução, em vez de sempre iniciar recolhido.

## Impact

- `src/b3_selic_pre/presentation/settings.py`: detecção de primeira execução e separação entre defaults de primeira execução e defaults de compatibilidade.
- `tests/test_settings.py`: cobertura dos novos defaults, da preservação de arquivos existentes e do comportamento de arquivos corrompidos.
- Nenhuma mudança em `domain`, `application`, `infrastructure`, dependências externas ou formato de dados.
- Nenhum teste de UI novo é necessário; o estado inicial continua sendo aplicado pela GUI a partir de `Settings`.
