# Spec Delta

## MODIFIED Requirements

### Requirement: Subcomandos de verbo e GUI como padrão

A CLI SHALL organizar suas operações em subcomandos de verbo: `consultar`, `atualizar`, `exportar`, `mcp`, `tesouro`, `tesouro-resgates`, `tesouro-estoque`, `mercado`, `gui` e `criar-atalho`.

#### Scenario: Execução sem argumentos abre a GUI
- **WHEN** o usuário executa `b3-selic-pre` sem argumentos
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Subcomando gui abre a GUI
- **WHEN** o usuário executa `b3-selic-pre gui`
- **THEN** a interface gráfica SHALL ser iniciada

#### Scenario: Ajuda lista os subcomandos
- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar os subcomandos disponíveis e seus parâmetros

## ADDED Requirements

### Requirement: Subcomando mercado

A CLI SHALL aceitar o subcomando `mercado` para consultar ou exportar séries de dólar e ouro.

O subcomando SHALL aceitar `--ativo usd|ouro|ambos` (padrão `ambos`), `--inicio`, `--fim`, `--resolucao auto|dia|semana|mes` (padrão `auto`), `--prever`, `--formato csv|json` (padrão `csv`), `--saida`, `--no-cache` e `--atualizar`.

Sem `--inicio` e `--fim`, a janela SHALL ser os 12 meses anteriores à maior data disponível no cache. Sem `--atualizar` nem `--no-cache`, o comando NÃO SHALL acessar a rede.

#### Scenario: Ajuda lista o subcomando

- **WHEN** o usuário executa `b3-selic-pre --help`
- **THEN** a saída SHALL listar `mercado`
- **THEN** a ajuda SHALL listar as opções aceitas

#### Scenario: Janela padrão

- **WHEN** o usuário executa `mercado` sem `--inicio` e `--fim`
- **THEN** a saída SHALL cobrir os 12 meses anteriores à maior data em cache

#### Scenario: Filtro de ativo

- **WHEN** o usuário executa `mercado --ativo ouro`
- **THEN** a saída SHALL conter apenas a série de ouro

#### Scenario: Cenário incluído

- **WHEN** o usuário executa `mercado --prever`
- **THEN** a saída SHALL incluir o cenário de 12 meses
- **THEN** o cenário SHALL ser identificado como projeção, não como recomendação

#### Scenario: Atualização antes da saída

- **WHEN** o usuário executa `mercado --atualizar`
- **THEN** a CLI SHALL buscar as fontes antes de emitir a saída
- **THEN** a CLI SHALL gravar o cache bruto e disparar o pré-cálculo

#### Scenario: Sem rede por padrão

- **WHEN** o usuário executa `mercado` sem `--atualizar` e sem `--no-cache`
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

### Requirement: Formatos e saída do subcomando mercado

O formato CSV de histórico SHALL ter delimitador `;`, datas ISO e colunas `DATA;ATIVO;VALOR;UNIDADE;ORIGEM;METODO`.

O formato CSV de cenário SHALL ter colunas `DATA;ATIVO;CENARIO;INFERIOR_80;SUPERIOR_80;INFERIOR_95;SUPERIOR_95;METODO`. O formato JSON SHALL conter `janela`, `series`, `previsao`, `indicadores`, `origem` e `gerado_em`.

#### Scenario: CSV de histórico

- **WHEN** `mercado` é executado sem `--prever`
- **THEN** a saída SHALL ser o CSV de histórico
- **THEN** os valores numéricos SHALL usar ponto decimal

#### Scenario: CSV de cenário

- **WHEN** `mercado --prever --formato csv` é executado
- **THEN** a saída SHALL conter o CSV de cenário
- **THEN** as bandas de 80% e 95% SHALL estar presentes

#### Scenario: JSON estruturado

- **WHEN** `mercado --formato json` é executado
- **THEN** a saída SHALL ser um objeto JSON com séries, cenário e indicadores
- **THEN** a origem e o tipo de projeção SHALL estar presentes

#### Scenario: Um artefato vai para stdout

- **WHEN** exatamente um artefato é selecionado e `--saida` não é informado
- **THEN** o artefato SHALL ser impresso no stdout

#### Scenario: Vários artefatos exigem diretório

- **WHEN** `--prever` gera histórico e cenário e `--saida` não é um diretório
- **THEN** a CLI SHALL encerrar com código `2`

#### Scenario: Nomes padrão

- **WHEN** `--saida` é um diretório
- **THEN** os arquivos SHALL ser `mercado-historico.csv`, `mercado-previsao.csv` ou `mercado.json`, conforme o formato

#### Scenario: Falha de escrita

- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** a CLI SHALL encerrar com código `1` e mensagem em `stderr`
