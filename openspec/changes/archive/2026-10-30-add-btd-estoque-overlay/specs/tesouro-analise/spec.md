# Spec Delta

## ADDED Requirements

### Requirement: Sobreposição BTD na série de estoque

O pré-cálculo da série de estoque SHALL considerar os registros agregados do BTD que não existem no CKAN. A série resultante SHALL usar a maior data disponível entre as duas fontes e SHALL permanecer independente de janela, sem acesso à rede durante o cálculo ou a leitura.

#### Scenario: Série com mês do BTD

- **WHEN** a sobreposição BTD contém um mês ausente no CKAN
- **THEN** a série de estoque SHALL conter esse mês
- **THEN** os percentuais do mês SHALL ser calculados sobre o total dos títulos presentes no BTD
- **THEN** os meses anteriores SHALL permanecer calculados a partir do CKAN

#### Scenario: Sem sobreposição

- **WHEN** não há sobreposição BTD ou ela não acrescenta meses
- **THEN** a série de estoque SHALL ser idêntica à calculada somente com o CKAN

#### Scenario: Leitura sem rede

- **WHEN** a série de estoque é lida para exibição
- **THEN** nenhum XLSX ou página do BTD SHALL ser baixado
- **THEN** nenhuma fonte alternativa SHALL ser consultada

### Requirement: Invalidação da série pela sobreposição BTD

A partição analítica `estoque` SHALL considerar o hash do arquivo normalizado do BTD, quando existir, além do hash do CSV do CKAN. Alteração ou remoção da sobreposição SHALL invalidar apenas a série de estoque; demanda e fluxo NÃO SHALL ser recalculados.

#### Scenario: Sobreposição mudou

- **WHEN** o hash do arquivo normalizado do BTD muda
- **THEN** a partição `estoque` SHALL ser recalculada no próximo refresh
- **THEN** as partições `demanda` e `fluxo` SHALL permanecer reutilizáveis

#### Scenario: Sobreposição ausente

- **WHEN** não existe arquivo normalizado do BTD
- **THEN** a partição `estoque` SHALL continuar válida usando apenas o CKAN
- **THEN** a ausência do BTD NÃO SHALL invalidar a série indefinidamente

#### Scenario: Retenção de 3 anos

- **WHEN** o mês mais recente vem do BTD
- **THEN** o corte de retenção SHALL ser calculado a partir desse mês
- **THEN** meses fora da retenção NÃO SHALL compor a série

#### Scenario: Housekeeping após refresh

- **WHEN** o refresh do estoque conclui com a sobreposição BTD
- **THEN** o housekeeping SHALL usar a maior data disponível entre CKAN e BTD
- **THEN** nenhum arquivo SHALL ser removido antes da nova série ser gravada
