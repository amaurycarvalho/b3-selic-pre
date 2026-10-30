# Spec Delta

## MODIFIED Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `tesouro-resgates`, `tesouro-estoque`, `mercado`, `reservas`, `gui` e `criar-atalho`.

#### Scenario: Execução sem argumentos abre a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Subcomando gui abre a GUI
- **WHEN** o usuário executa `b3-selic-pre gui`
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Ajuda lista os subcomandos
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar os subcomandos disponíveis e seus parâmetros

#### Scenario: Ajuda lista reservas
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `reservas`

## ADDED Requirements

### Requirement: Subcomando reservas

A CLI SHALL aceitar o subcomando `reservas` para consultar ou exportar a série de reservas internacionais.

O subcomando SHALL aceitar `--inicio`, `--fim`, `--janela 12m|3a`, `--formato csv|json`, `--saida`, `--no-cache` e `--atualizar`. Sem `--atualizar` nem `--no-cache`, o comando NÃO SHALL acessar a rede.

#### Scenario: Janela padrão

- **WHEN** o usuário executa `reservas` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os 12 meses anteriores à maior data em cache

#### Scenario: Janela de três anos

- **WHEN** o usuário executa `reservas --janela 3a`
- **THEN** a saída SHALL cobrir até 36 meses anteriores à maior data em cache

#### Scenario: Atualização antes da saída

- **WHEN** o usuário executa `reservas --atualizar`
- **THEN** a CLI SHALL buscar a série antes de emitir a saída
- **THEN** a CLI SHALL gravar o cache bruto e disparar o pré-cálculo

#### Scenario: Sem rede por padrão

- **WHEN** o usuário executa `reservas` sem `--atualizar` e sem `--no-cache`
- **THEN** nenhuma requisição de rede SHALL ser iniciada

#### Scenario: Sem dados em cache

- **WHEN** não há dados para a janela solicitada
- **THEN** a CLI SHALL encerrar com código `1` e mensagem em `stderr`
- **THEN** a mensagem SHALL orientar o uso de `--atualizar`

#### Scenario: Datas inválidas

- **WHEN** `--inicio` ou `--fim` está fora do formato `AAAA-MM-DD`
- **THEN** a CLI SHALL encerrar com código `2`
- **THEN** nenhuma busca SHALL ser iniciada

#### Scenario: Início posterior ao fim

- **WHEN** `--inicio` é posterior a `--fim`
- **THEN** a CLI SHALL encerrar com código `2`

### Requirement: Formatos e saída do subcomando reservas

O formato CSV SHALL usar delimitador `;`, datas ISO e colunas `DATA;VALOR;UNIDADE;ORIGEM;METODO`.

O formato JSON SHALL conter `janela`, `serie`, `indicadores`, `origem` e `gerado_em`. As regras de `--saida` SHALL seguir o subcomando `exportar`, com nomes padrão `reservas-serie.csv` e `reservas.json`.

#### Scenario: CSV de série

- **WHEN** `reservas` é executado sem `--formato json`
- **THEN** a saída SHALL ser o CSV de série
- **THEN** os valores numéricos SHALL usar ponto decimal

#### Scenario: JSON estruturado

- **WHEN** `reservas --formato json` é executado
- **THEN** a saída SHALL ser um objeto JSON com série, indicadores e origem

#### Scenario: Um artefato vai para stdout

- **WHEN** `--saida` não é informado
- **THEN** o artefato SHALL ser impresso no stdout

#### Scenario: Nomes padrão em diretório

- **WHEN** `--saida` é um diretório
- **THEN** o arquivo SHALL ser `reservas-serie.csv` ou `reservas.json`, conforme o formato

#### Scenario: Falha de escrita

- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** a CLI SHALL encerrar com código `1` e mensagem em `stderr`
