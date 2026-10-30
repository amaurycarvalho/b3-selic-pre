# Spec Delta

## Purpose

Obter do Balanço do Tesouro Direto (BTD) a posição mensal de estoque por título mais recente que o dataset CKAN e disponibilizá-la como sobreposição para a análise de estoque, preservando o CKAN como fonte canônica e detalhada.

## ADDED Requirements

### Requirement: Descoberta da publicação BTD mais recente

O sistema SHALL obter a edição mais recente da publicação `Balanco do Tesouro Direto (BTD)` a partir da página pública de publicações, localizar o anexo XLSX dessa edição e validar que o conteúdo é uma planilha válida antes de usá-lo. O parsing da página SHALL limitar-se a identificar a edição, a data de publicação e o link do anexo XLSX; nenhum conteúdo adicional do HTML SHALL ser interpretado.

#### Scenario: Edição mais recente disponível

- **WHEN** a página base da publicação responde com a edição mais recente
- **THEN** o sistema SHALL identificar o mês de referência da edição
- **THEN** o sistema SHALL localizar o anexo XLSX da edição
- **THEN** o sistema SHALL registrar a URL do anexo e a data de publicação

#### Scenario: Anexo XLSX ausente ou inválido

- **WHEN** a edição não possui anexo XLSX ou o download não é uma planilha válida
- **THEN** o sistema SHALL falhar a atualização da fonte BTD
- **THEN** nenhum dado parcial do BTD SHALL ser cacheado
- **THEN** o cache BTD anterior SHALL permanecer disponível

#### Scenario: Página fora do formato esperado

- **WHEN** a página não contém a edição, o mês de referência ou o link do anexo
- **THEN** o sistema SHALL classificar como falha de dados da fonte BTD
- **THEN** nenhuma fonte alternativa ou scraping adicional SHALL ser usado

### Requirement: Parsing do estoque por título do BTD

O sistema SHALL ler a aba de estoque por título do XLSX do BTD e produzir registros mensais com `tipo_titulo`, `mes` e `valor_estoque`. O mês SHALL ser convertido de `MMM/AA` para `AAAA-MM`; os valores em R$ milhões SHALL ser convertidos para reais. Linhas de total/agregado da seção, como `Estoque` ou `Total`, NÃO SHALL ser tratadas como títulos.

#### Scenario: Aba de estoque identificada

- **WHEN** o XLSX é aberto
- **THEN** o sistema SHALL identificar a aba `2.1 - Estoque por Título`
- **THEN** o sistema SHALL ler o cabeçalho de meses e a seção de valores em R$ milhões
- **THEN** a seção percentual da mesma aba NÃO SHALL ser confundida com valores absolutos
- **THEN** a linha de total/agregado `Estoque` NÃO SHALL ser lida como um título

#### Scenario: Histórico mensal disponível

- **WHEN** a planilha contém meses anteriores ao maior mês do CKAN
- **THEN** o sistema SHALL normalizar todos os meses presentes na seção de valores
- **THEN** o histórico normalizado SHALL ficar disponível no cache BTD

#### Scenario: Título desconhecido

- **WHEN** a planilha contém um `tipo_titulo` fora da taxonomia conhecida
- **THEN** o sistema SHALL preservar o título
- **THEN** o sistema SHALL classificá-lo como `OUTROS` na análise
- **THEN** o sistema SHALL registrar um aviso, sem descartar o registro

#### Scenario: Planilha sem a aba ou sem registros

- **WHEN** a aba de estoque não existe ou não há registros de valor
- **THEN** o sistema SHALL classificar como falha de dados da fonte BTD
- **THEN** nenhum cache BTD SHALL ser gravado

### Requirement: Cache normalizado do BTD

O sistema SHALL manter um cache próprio do estoque BTD normalizado, com gravação atômica, metadados de proveniência e TTL de 24 horas. Falha de atualização NÃO SHALL descartar o cache anterior.

#### Scenario: Cache fresco

- **WHEN** o cache BTD tem menos de 24 horas
- **THEN** o sistema SHALL reutilizá-lo sem acessar a rede

#### Scenario: Cache vencido

- **WHEN** o cache BTD tem 24 horas ou mais
- **THEN** o sistema SHALL tentar atualizar a publicação
- **THEN** em caso de sucesso, o novo conteúdo SHALL substituir o anterior atomicamente
- **THEN** em caso de falha, o conteúdo anterior SHALL ser preservado

#### Scenario: Leitura somente cache

- **WHEN** a sub-aba `Estoque` é exibida pela primeira vez
- **THEN** o sistema SHALL ler o cache BTD sem acessar a rede
- **THEN** o cache ausente SHALL ser tratado como ausência da sobreposição, não como erro do CKAN

#### Scenario: Proveniência registrada

- **WHEN** o cache BTD é gravado
- **THEN** os metadados SHALL conter mês de referência, data de publicação, URL da edição, URL do anexo e `sha256` do XLSX

### Requirement: Sobreposição sem substituição do CKAN

O sistema SHALL combinar o estoque detalhado do CKAN com os registros agregados do BTD, acrescentando apenas registros de meses posteriores ao maior mês existente no CKAN. Meses já cobertos pelo CKAN NÃO SHALL receber registros do BTD, mesmo quando os títulos agregados do BTD tiverem nomes diferentes dos títulos detalhados do CKAN; registros do CKAN NÃO SHALL ser substituídos por valores do BTD.

#### Scenario: BTD mais recente

- **WHEN** o BTD contém um mês posterior ao maior mês do CKAN
- **THEN** os títulos desse mês SHALL ser acrescentados ao conjunto usado pela análise
- **THEN** a maior data disponível SHALL passar a ser o mês do BTD

#### Scenario: Meses coincidentes

- **WHEN** BTD e CKAN contêm dados do mesmo mês, inclusive com títulos agregados de nomes diferentes
- **THEN** o valor do CKAN SHALL ser mantido
- **THEN** o valor do BTD NÃO SHALL gerar um registro duplicado

#### Scenario: BTD sem novidade

- **WHEN** todos os meses do BTD já existem no CKAN
- **THEN** nenhum registro SHALL ser acrescentado
- **THEN** a data-base e a análise SHALL permanecer as do CKAN

### Requirement: Falha do BTD não bloqueia o estoque

A indisponibilidade da fonte BTD NÃO SHALL impedir a atualização, a leitura ou a exibição do estoque do CKAN. A falha SHALL ser comunicada como aviso não bloqueante e o cache BTD anterior SHALL continuar utilizável.

#### Scenario: Falha no refresh do BTD

- **WHEN** a descoberta, o download ou o parsing do BTD falha durante uma atualização
- **THEN** o refresh do CKAN SHALL permanecer bem-sucedido
- **THEN** a sobreposição BTD anterior SHALL continuar disponível
- **THEN** a statusbar SHALL informar que a complementação BTD não foi atualizada

#### Scenario: Falha sem cache BTD

- **WHEN** não há cache BTD e a atualização do BTD falha
- **THEN** a análise SHALL usar somente o CKAN
- **THEN** o refresh NÃO SHALL ser considerado falho por causa do BTD
