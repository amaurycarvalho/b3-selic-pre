## ADDED Requirements

### Requirement: Testes de comportamento migrados de UI para headless

Testes que validam regras de negócio, exportação, estatísticas, dispatch de gráfico ou estado derivado de controles SHALL ser migrados para testes headless. Apenas testes de montagem, aparência e wiring de widgets SHALL permanecer como testes de UI. Após a migração, o orçamento de testes de UI SHALL ser reduzido para a nova contagem.

#### Scenario: Comportamento testado sem display

- **WHEN** um teste valida validação de data, seleção de exportação, estatísticas, modo de gráfico ou estado de habilitação
- **THEN** ele executa sem Tkinter e sem display
- **THEN** ele importa o serviço/view-model headless correspondente

#### Scenario: UI mantém apenas testes de apresentação

- **WHEN** um teste de UI é mantido
- **THEN** ele valida montagem, existência/configuração de widgets ou wiring com o view-model
- **THEN** regras de negócio já são cobertas por testes headless

#### Scenario: Orçamento reduzido após migração

- **WHEN** os testes migrados deixam de depender de Tkinter
- **THEN** `UI_TEST_BUDGET` é reduzido para a contagem real de testes de UI remanescentes
- **THEN** o teste de guarda do orçamento continua passando
