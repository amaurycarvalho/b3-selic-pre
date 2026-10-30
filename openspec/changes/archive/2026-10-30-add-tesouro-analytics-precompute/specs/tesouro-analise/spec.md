## ADDED Requirements

### Requirement: Pré-cálculo incremental de séries por fonte

Após um refresh bem-sucedido, o sistema SHALL pré-calcular séries normalizadas para as fontes atualizadas: estoque, demanda de vendas e fluxo de vendas menos resgates. Cada série SHALL ser gravada no cache analítico com o `sha256` do CSV bruto que a originou. Fontes cujo conteúdo não mudou NÃO SHALL ser recalculadas.

#### Scenario: Fonte alterada

- **WHEN** o `sha256` do CSV bruto de uma fonte muda após o refresh
- **THEN** apenas as séries dessa fonte SHALL ser recalculadas
- **THEN** as séries das demais fontes SHALL permanecer reutilizáveis

#### Scenario: Conteúdo inalterado

- **WHEN** o refresh recebe `304` ou o CSV bruto permanece idêntico
- **THEN** nenhuma série SHALL ser recalculada

#### Scenario: Falha no pré-cálculo

- **WHEN** o pré-cálculo de uma fonte falha
- **THEN** o refresh SHALL permanecer bem-sucedido
- **THEN** a série válida anterior SHALL continuar legível
- **THEN** nenhuma fonte alternativa ou acesso de rede SHALL ser usado

### Requirement: Séries independentes de janela

As séries pré-calculadas SHALL ser independentes da janela selecionada, no menor bucket necessário por métrica, para que 14d, 3m, 12m e 3a sejam obtidas por filtragem e agregação sem novo parse do CSV bruto. O período SHALL permanecer ancorado na maior data disponível, sem datas futuras.

#### Scenario: Todas as janelas

- **WHEN** o usuário alterna entre 14d, 3m, 12m e 3a
- **THEN** todas as janelas SHALL usar as mesmas séries pré-calculadas
- **THEN** nenhum CSV bruto SHALL ser lido ou parseado

#### Scenario: Sem projeção

- **WHEN** uma série pré-calculada é gerada
- **THEN** ela SHALL conter apenas períodos observados
- **THEN** nenhum período futuro SHALL ser gerado

#### Scenario: Leitura somente leitura

- **WHEN** as séries pré-calculadas são lidas para exibição
- **THEN** nenhum arquivo SHALL ser removido, renomeado ou alterado
- **THEN** nenhuma requisição de rede SHALL ser feita
