## ADDED Requirements

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
