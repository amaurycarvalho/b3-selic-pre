## ADDED Requirements

### Requirement: Leitura de cache sem mutação

O sistema SHALL oferecer leitura do cache em modo somente leitura. Nesse modo, uma entrada ausente, vencida, corrompida ou incompleta SHALL ser tratada como miss, sem remover, renomear ou alterar o arquivo.

A leitura somente leitura NÃO SHALL acessar a rede nem disparar download.

#### Scenario: Entrada corrompida é miss sem remoção

- **WHEN** um arquivo de cache contém JSON inválido em modo somente leitura
- **THEN** a leitura SHALL devolver miss
- **THEN** o arquivo SHALL permanecer no disco

#### Scenario: Entrada incompleta é miss

- **WHEN** uma entrada não satisfaz os metadados de completude
- **THEN** a leitura SHALL devolver miss
- **THEN** o arquivo NÃO SHALL ser removido

#### Scenario: Leitura não acessa a rede

- **WHEN** uma data não está no cache em modo somente leitura
- **THEN** a leitura SHALL devolver miss
- **THEN** nenhuma requisição SHALL ser feita à B3

### Requirement: Escrita atômica de cache

A gravação de uma entrada de cache SHALL ser atômica. Um leitor concorrente SHALL ver a entrada anterior completa ou a nova entrada completa, nunca um conteúdo parcial.

A escrita atômica SHALL preservar a validação de completude e a política de não gravar resultados vazios ou parciais.

#### Scenario: Leitor concorrente não vê conteúdo parcial

- **WHEN** uma entrada de cache está sendo gravada enquanto outro processo lê a mesma data
- **THEN** o leitor SHALL ver a entrada anterior ou a nova
- **THEN** o leitor NÃO SHALL interpretar a entrada como corrompida por causa da escrita

#### Scenario: Resultado vazio não é gravado

- **WHEN** uma carga termina sem registros
- **THEN** nenhuma entrada de cache SHALL ser criada ou substituída
