## Purpose

Fornecer serviços de aplicação, transformações de dados e estado de apresentação que possam ser exercitados sem Tkinter ou matplotlib, permitindo que GUI e futuros comandos CLI compartilhem as mesmas regras e que a maior parte da suíte seja headless.

## ADDED Requirements

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

### Requirement: CLI atua como composition root reutilizando casos de uso

A CLI SHALL interpretar parâmetros, montar adapters de infraestrutura e invocar serviços da camada `application`, sem reimplementar validação, transformação ou formatação de negócio. Novos comandos por parâmetro SHALL seguir esse mesmo caminho.

#### Scenario: Comando CLI usa serviço compartilhado

- **WHEN** um comando CLI consulta taxas, exporta dados ou valida uma data
- **THEN** ele chama o serviço de aplicação já usado pela GUI
- **THEN** a lógica de negócio não é duplicada na CLI

#### Scenario: Adapter injetado no composition root

- **WHEN** a CLI precisa do cliente B3 ou do criador de atalho
- **THEN** ela instancia o adapter no composition root e o injeta no serviço/caso de uso
- **THEN** os módulos de application não importam infrastructure

### Requirement: GUI consome apenas API pública da aplicação

A presentation SHALL importar casos de uso e formatação por seus módulos públicos, sem depender de módulos privados (`_config`, `_texto_evolucao`, etc.) para orquestrar regras.

#### Scenario: Evolução renderizada via API pública

- **WHEN** a GUI monta o resumo de evolução da curva
- **THEN** ela usa a API pública de `application.analyze`
- **THEN** não importa `application.analyze._texto_evolucao`
