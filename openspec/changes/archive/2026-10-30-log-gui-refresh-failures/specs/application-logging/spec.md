# Spec Delta

## ADDED Requirements

### Requirement: Registro de falhas de atualização na GUI

Falhas de leitura de cache, de atualização e de fontes parciais nas sub-abas de dados da interface gráfica SHALL ser registradas no arquivo ativo de log, identificando a sub-aba e a operação afetada.

O registro SHALL seguir a classificação de `Falhas de comunicação em linha única`: falhas de comunicação sem traceback e demais defeitos com traceback. A mesma exceção NÃO SHALL ser registrada mais de uma vez.

#### Scenario: Falha ao atualizar o Tesouro Direto

- **WHEN** o `Atualizar` de uma sub-aba do Tesouro Direto falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de atualização
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha ao ler o cache do Tesouro Direto

- **WHEN** a leitura do cache de uma sub-aba do Tesouro Direto falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de leitura de cache
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha ao atualizar Câmbio e Reservas

- **WHEN** o `Atualizar` da sub-aba Dólar e Ouro ou Reservas Internacionais falha
- **THEN** o log ativo SHALL registrar a sub-aba e a operação de atualização
- **THEN** a statusbar SHALL continuar exibindo a falha ao usuário

#### Scenario: Falha parcial de fonte

- **WHEN** uma fonte do Tesouro, de mercado ou de reservas falha e as demais respondem
- **THEN** o log ativo SHALL registrar a fonte que falhou
- **THEN** os dados disponíveis SHALL continuar sendo exibidos
- **THEN** a statusbar SHALL continuar identificando a fonte com falha

#### Scenario: Falha de comunicação sem traceback

- **WHEN** a falha registrada é de comunicação
- **THEN** o log SHALL conter uma única linha com o tipo e a mensagem da exceção
- **THEN** o registro NÃO SHALL conter traceback

#### Scenario: Defeito inesperado com traceback

- **WHEN** a falha registrada não é de comunicação
- **THEN** o log SHALL conter o traceback completo da exceção

#### Scenario: Registro único por exceção

- **WHEN** a mesma exceção atravessa controller e GUI
- **THEN** ela SHALL ser registrada uma única vez no arquivo ativo
