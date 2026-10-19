# Architecture Governance

## Purpose

Define as regras de dependência entre as camadas da aplicação, o mecanismo de aprovação explícita de exceções e o protocolo mínimo de validação que toda change deve cumprir para preservar a Clean Architecture e a testabilidade headless.

## Requirements

### Requirement: Dependências entre camadas seguem a Clean Architecture

O projeto SHALL manter as dependências apontando para dentro: `domain` não pode importar `application`, `infrastructure` ou `presentation`; `application` não pode importar `infrastructure` ou `presentation`; `infrastructure` não pode importar `presentation`; `presentation` pode importar `domain` e `application`. Pontos de entrada executáveis (`__main__`) e composition roots podem montar dependências externas explicitamente.

#### Scenario: Camada interna importa camada externa não aprovada

- **WHEN** um módulo de `domain`, `application` ou `infrastructure` importa um módulo de uma camada externa não permitida
- **THEN** o teste de guarda de arquitetura falha indicando o módulo importador e a camada importada
- **THEN** a change não pode ser concluída sem corrigir a dependência ou registrar uma aprovação explícita

#### Scenario: Dependências permitidas passam na guarda

- **WHEN** `application` importa apenas `domain`/`application` e `presentation` importa apenas `domain`/`application`/`presentation`
- **THEN** o teste de guarda de arquitetura passa

### Requirement: Exceções de fronteira exigem aprovação explícita

O projeto SHALL manter um arquivo de aprovações explícitas, versionado, com a justificativa de cada violação conhecida de camada ou de importação externa proibida. Uma nova exceção SHALL exigir alteração explícita desse arquivo em revisão de código. Entradas obsoletas SHALL ser removidas.

#### Scenario: Nova violação sem aprovação

- **WHEN** uma nova violação de camada é introduzida sem entrada correspondente no arquivo de aprovações
- **THEN** o teste de guarda falha e informa como corrigir ou solicitar aprovação

#### Scenario: Aprovação obsoleta após refatoração

- **WHEN** uma dívida aprovada é corrigida e a entrada permanece no arquivo de aprovações
- **THEN** o teste de guarda falha solicitando a remoção da entrada obsoleta

### Requirement: Camadas internas permanecem headless e puras

A camada `domain` SHALL ser pura, sem I/O, UI, rede ou frameworks. A camada `application` SHALL ser headless, sem `tkinter`, `matplotlib`, bibliotecas de clipboard ou acesso direto à rede. A camada `infrastructure` SHALL NOT depender de UI.

#### Scenario: Domain importa I/O ou framework

- **WHEN** `domain` importa módulos de sistema operacional, arquivos, rede, UI ou frameworks não aprovados
- **THEN** o teste de guarda de pureza falha

#### Scenario: Application importa UI ou rede

- **WHEN** `application` importa `tkinter`, `matplotlib`, clipboard ou cliente HTTP/rede
- **THEN** o teste de guarda headless falha

### Requirement: Regras de negócio são reutilizáveis por GUI e CLI

Regras de negócio SHALL residir na camada `application` e ser consumidas pela `presentation`, de modo que a futura implementação de comandos por parâmetros de CLI reutilize os mesmos casos de uso da GUI sem duplicar lógica. A `presentation` SHALL limitar-se a interpretar entrada, montar dependências externas e renderizar saída.

#### Scenario: Novo comando CLI reutiliza regra existente

- **WHEN** um comando por parâmetro da CLI precisa de validação, transformação de dados ou formatação já usada pela GUI
- **THEN** ele chama o mesmo serviço/caso de uso da camada `application`
- **THEN** nenhuma regra de negócio é reimplementada na `presentation`

#### Scenario: Regra de negócio testada sem display

- **WHEN** uma regra de negócio da aplicação é validada
- **THEN** o teste correspondente executa sem Tkinter e sem display gráfico

### Requirement: Toda change executa validação mínima obrigatória

Toda change SHALL executar, ao final da implementação, `make lint` e `make complexity`, além dos testes diretamente relacionados ao código impactado. A suíte completa SHALL ser executada somente quando a change alterar código compartilhado ou contratos capazes de causar regressão na aplicação (por exemplo `domain`, interfaces entre camadas, infraestrutura comum ou comportamento global da GUI/CLI).

#### Scenario: Change sem risco de regressão ampla

- **WHEN** a change altera apenas código ou testes localizados e não justifica a suíte completa
- **THEN** a implementação executa `make lint`, `make complexity` e os testes ligados diretamente ao código impactado
- **THEN** a change registra como passo final um teste manual opcional para o usuário

#### Scenario: Change com risco de regressão

- **WHEN** a change altera código compartilhado ou contratos que podem afetar outras partes da aplicação
- **THEN** a implementação executa `make lint`, `make complexity` e a suíte completa de testes
- **THEN** a justificativa para a suíte completa fica registrada na change

#### Scenario: Falha na validação mínima

- **WHEN** `make lint`, `make complexity` ou um teste diretamente relacionado falha
- **THEN** a change não é considerada concluída
