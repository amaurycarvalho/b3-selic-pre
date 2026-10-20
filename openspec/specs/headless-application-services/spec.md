# Headless Application Services

## Purpose

Fornecer serviços de aplicação, transformações de dados e estado de apresentação que possam ser exercitados sem Tkinter ou matplotlib, permitindo que GUI e futuros comandos CLI compartilhem as mesmas regras e que a maior parte da suíte seja headless.

## Requirements

### Requirement: Configuração da aplicação é independente da presentation

A camada `application` SHALL construir suas configurações a partir de mappings ou valores simples fornecidos pela composição, sem importar `presentation`, `Settings`, Tkinter ou qualquer detalhe de persistência. A presentation SHALL montar a configuração a partir das preferências persistidas e passá-la aos casos de uso.

#### Scenario: Configuração construída sem Settings

- **WHEN** um caso de uso de análise precisa da configuração da curva
- **THEN** ele recebe a configuração já montada ou a constrói a partir de um mapping simples
- **THEN** nenhum módulo de `application` importa `presentation`

#### Scenario: GUI aplica preferências persistidas

- **WHEN** a GUI inicia uma análise usando as preferências do usuário
- **THEN** ela monta a configuração a partir de `Settings` e a injeta no caso de uso

### Requirement: Regras de data e histórico vivem na aplicação

Validação de formato de data, rejeição de datas futuras, limite de idade do histórico, cálculo da data útil mais próxima e janela de evolução SHALL ser serviços da camada `application`, reutilizáveis pela GUI e por comandos CLI.

#### Scenario: Data futura rejeitada sem GUI

- **WHEN** um serviço de consulta recebe uma data posterior à data corrente
- **THEN** ele rejeita a consulta com uma mensagem de validação
- **THEN** o comportamento é testável sem display

#### Scenario: Data útil calculada na aplicação

- **WHEN** uma data cai em fim de semana
- **THEN** a camada `application` retorna a data útil anterior
- **THEN** GUI e CLI usam o mesmo cálculo

### Requirement: Exportação e estatísticas são serviços da aplicação

A seleção do conteúdo exportado (bruto, consolidado por ano ou evolução) e o cálculo de estatísticas de taxas SHALL ser serviços da camada `application`/view-model headless, não dos mixins de GUI.

#### Scenario: Exportação consolidada sem Tk

- **WHEN** o modo de visualização é consolidado e há registros
- **THEN** o serviço de exportação retorna o CSV consolidado
- **THEN** o teste correspondente não instancia Tkinter

#### Scenario: Exportação sem dados

- **WHEN** não há registros nem histórico
- **THEN** o serviço de exportação indica que não há conteúdo a copiar
- **THEN** nenhum texto vazio é enviado ao clipboard

### Requirement: Transformações de dados de gráfico são headless

Cálculos de marcações de eixo, interpolação de taxas, seleção de taxa mais próxima, consolidação por ano e construção de grades 3D SHALL residir fora dos renderizadores matplotlib, em módulos importáveis sem display.

#### Scenario: Grade 3D calculada sem matplotlib

- **WHEN** um teste valida a grade consolidada ou diária da evolução 3D
- **THEN** ele importa apenas o módulo de dados de gráfico e não cria figura matplotlib

#### Scenario: Renderizador apenas desenha

- **WHEN** `presentation/charts.py` renderiza um gráfico
- **THEN** ele consome os dados já calculados pelo módulo headless
- **THEN** a lógica de interpolação/marcações não é duplicada na presentation

### Requirement: Estado da GUI é representado por view-model headless

O estado derivado da GUI (estatísticas exibidas, habilitação de controles, modo de gráfico e texto de exportação) SHALL ser calculado por um view-model/controlador sem imports de Tkinter, e a GUI SHALL apenas refletir esse estado em widgets.

#### Scenario: Estado de botões validado sem display

- **WHEN** registros são carregados, limpos ou uma busca falha
- **THEN** o view-model informa quais controles devem estar habilitados
- **THEN** o teste valida o estado sem criar uma janela Tk

#### Scenario: Modo de gráfico validado sem display

- **WHEN** o usuário alterna entre curva curta, curva longa, evolução, 3D ou análise
- **THEN** o view-model informa qual renderizador deve ser usado
- **THEN** o teste de dispatch não depende de widgets

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

### Requirement: GUI consome apenas API pública da aplicação

A presentation SHALL importar casos de uso e formatação por seus módulos públicos, sem depender de módulos privados (`_config`, `_texto_evolucao`, etc.) para orquestrar regras.

#### Scenario: Evolução renderizada via API pública

- **WHEN** a GUI monta o resumo de evolução da curva
- **THEN** ela usa a API pública de `application.analyze`
- **THEN** não importa `application.analyze._texto_evolucao`

### Requirement: Transformação headless para a curva longa

A camada de aplicação SHALL oferecer uma transformação pura que converte os registros brutos de uma curva na série de taxas médias por ano, com um ponto por ano, ordenado do ano mais curto para o mais longo.

A transformação SHALL estar disponível também para o histórico de datas, convertendo cada curva disponível. Ela NÃO SHALL importar `presentation`, `infrastructure`, Tkinter, matplotlib ou clientes de rede.

#### Scenario: Curva longa a partir de registros brutos

- **WHEN** a transformação recebe registros de múltiplos anos
- **THEN** ela SHALL produzir um ponto por ano com a taxa média anual
- **THEN** os pontos SHALL estar ordenados por ano

#### Scenario: Histórico convertido por data

- **WHEN** a transformação recebe um histórico de cinco datas
- **THEN** cada data SHALL ser convertida para a série de médias anuais
- **THEN** datas sem registros SHALL permanecer vazias

#### Scenario: Transformação sem display

- **WHEN** um teste exercita a transformação
- **THEN** ele SHALL importar apenas módulos de aplicação e domínio
- **THEN** nenhuma janela ou figura SHALL ser criada

### Requirement: Serviços headless para payloads do MCP

A camada de aplicação SHALL montar os payloads estruturados das tools a partir de registros, histórico, configuração e referência de data, incluindo paginação e o envelope de erros de domínio.

Os serviços NÃO SHALL implementar JSON-RPC, ler `stdin`, escrever `stdout` ou depender de `presentation`/`infrastructure`.

#### Scenario: Payload de curva

- **WHEN** a apresentação solicita o payload de `consultar_curva`
- **THEN** a aplicação SHALL devolver os itens e o cursor de continuação quando aplicável
- **THEN** a apresentação SHALL apenas serializar a resposta

#### Scenario: Payload de erro de domínio

- **WHEN** a apresentação solicita um erro de domínio recuperável
- **THEN** a aplicação SHALL devolver `motivo`, `detalhe` e `dica`
- **THEN** o payload NÃO SHALL conter `isError`

#### Scenario: Aplicação não conhece o protocolo

- **WHEN** um teste importa os serviços de payload
- **THEN** nenhum módulo de `presentation` ou `infrastructure` SHALL ser necessário

### Requirement: Análise selecionável por representação

O serviço de aplicação que monta o texto da análise SHALL aceitar a representação `curta` ou `longa`. Para `longa`, ele SHALL transformar tanto a curva atual quanto o histórico antes de calcular a análise e a evolução.

Se uma análise pré-calculada for fornecida, o serviço SHALL reutilizá-la somente quando a representação corresponder à solicitada; caso contrário, SHALL recalcular o texto.

#### Scenario: Análise longa usa o histórico convertido

- **WHEN** o serviço monta a análise longa com histórico
- **THEN** a estabilidade e a mudança de inclinação SHALL ser calculadas sobre as séries de médias anuais

#### Scenario: Análise pré-calculada de outra representação é ignorada

- **WHEN** a análise pré-calculada é curta e a solicitação é longa
- **THEN** o serviço SHALL recalcular a análise longa
- **THEN** o texto devolvido SHALL corresponder à curva longa
