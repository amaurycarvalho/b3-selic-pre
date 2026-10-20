## ADDED Requirements

### Requirement: Serviços headless de análise e exportação da CLI

A camada `application` SHALL oferecer serviços importáveis sem Tkinter ou matplotlib para:

- montar o texto determinístico da análise da curva;
- montar o texto da evolução da curva;
- formatar a evolução detalhada como CSV;
- selecionar os artefatos de exportação da CLI.

Esses serviços NÃO SHALL importar `presentation`, `infrastructure`, Tkinter ou matplotlib.

#### Scenario: Análise textual sem display
- **WHEN** um teste monta o texto de análise a partir de registros e configuração
- **THEN** ele importa apenas módulos de `application`
- **THEN** nenhuma janela ou figura é criada

#### Scenario: Evolução textual sem display
- **WHEN** um teste monta o texto da evolução entre duas datas
- **THEN** ele importa apenas módulos de `application`
- **THEN** nenhuma janela ou figura é criada

#### Scenario: CSV detalhado da evolução sem Tk
- **WHEN** um teste formata a evolução detalhada das cinco datas
- **THEN** o resultado contém as colunas `DATA;DU252;DC365;TAXA`
- **THEN** o teste não instancia Tkinter

#### Scenario: Seleção de artefatos sem infraestrutura
- **WHEN** a CLI solicita os conteúdos de exportação
- **THEN** o serviço de aplicação retorna os textos e CSVs selecionados
- **THEN** a gravação em arquivo permanece na camada de apresentação

## MODIFIED Requirements

### Requirement: CLI atua como composition root reutilizando casos de uso

A CLI SHALL interpretar subcomandos e parâmetros, montar adapters de infraestrutura e invocar serviços da camada `application`, sem reimplementar validação, transformação ou formatação de negócio. Novos subcomandos SHALL seguir esse mesmo caminho.

#### Scenario: Comando CLI usa serviço compartilhado

- **WHEN** um comando CLI consulta taxas, atualiza a evolução, exporta dados ou valida uma data
- **THEN** ele chama o serviço de aplicação já usado pela GUI
- **THEN** a lógica de negócio não é duplicada na CLI

#### Scenario: Adapter injetado no composition root

- **WHEN** a CLI precisa do cliente B3 ou do criador de atalho
- **THEN** ela instancia o adapter no composition root e o injeta no serviço/caso de uso
- **THEN** os módulos de application não importam infrastructure

#### Scenario: Exportação não grava arquivos na aplicação

- **WHEN** a CLI exporta um ou mais artefatos
- **THEN** a aplicação produz o conteúdo
- **THEN** somente a apresentação decide stdout, diretório e nomes de arquivo
