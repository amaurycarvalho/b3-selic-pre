# Spec Delta

## Purpose

Garantir que falhas de ajuste automático de layout nos gráficos sejam registradas no log e não apareçam como avisos técnicos para o usuário, preservando um desenho utilizável.

## ADDED Requirements

### Requirement: Avisos de layout são registrados

Quando o matplotlib informa que o ajuste automático de layout não pôde ser aplicado, o sistema SHALL registrar a ocorrência no log com o contexto do gráfico. O aviso técnico NÃO SHALL ser exibido ao usuário.

#### Scenario: Margens insuficientes

- **WHEN** um gráfico não comporta títulos, legendas ou rótulos nas margens disponíveis
- **THEN** o sistema SHALL registrar um aviso no log identificando o gráfico afetado
- **THEN** o aviso `Tight layout not applied` NÃO SHALL aparecer para o usuário

### Requirement: Layout alternativo após falha de ajuste

Após um aviso de layout não aplicável ou uma falha ao ajustar o layout, o sistema SHALL aplicar margens conservadoras e SHALL continuar o desenho do gráfico.

#### Scenario: Fallback aplicado

- **WHEN** o ajuste automático de layout não puder ser aplicado
- **THEN** o sistema SHALL aplicar margens conservadoras ao gráfico
- **THEN** o desenho SHALL prosseguir sem interrupção

#### Scenario: Falha ao aplicar o layout

- **WHEN** ocorrer um erro ao executar o ajuste de layout ou as margens de fallback
- **THEN** o erro SHALL ser registrado no log
- **THEN** o restante do desenho NÃO SHALL ser interrompido

### Requirement: Outros avisos são preservados

Avisos do matplotlib diferentes de `Tight layout not applied` SHALL continuar sendo emitidos normalmente.

#### Scenario: Aviso não relacionado

- **WHEN** o ajuste de layout emitir um aviso diferente de `Tight layout not applied`
- **THEN** o aviso SHALL ser reemitido ao usuário
- **THEN** margens de fallback NÃO SHALL ser aplicadas por causa desse aviso
