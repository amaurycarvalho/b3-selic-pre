# Linha de Comando (CLI)

Documentação técnica dos subcomandos, parâmetros e formatos de saída do
`b3-selic-pre`.

## Sinopse

```text
b3-selic-pre                         # abre a GUI
b3-selic-pre gui                     # abre a GUI
b3-selic-pre consultar [opções]
b3-selic-pre atualizar [opções]
b3-selic-pre exportar [opções]
b3-selic-pre tesouro [opções]
b3-selic-pre tesouro-resgates [opções]
b3-selic-pre tesouro-estoque [opções]
b3-selic-pre mercado [opções]
b3-selic-pre reservas [opções]
b3-selic-pre feriados [opções]
b3-selic-pre mcp [opções]
b3-selic-pre criar-atalho
b3-selic-pre --help
b3-selic-pre --version
```

Executar sem argumentos é equivalente a `gui`.

## Subcomandos

| Subcomando     | Finalidade                                                                       |
| -------------- | -------------------------------------------------------------------------------- |
| `consultar`    | Consulta as taxas de uma data e imprime CSV no terminal.                         |
| `atualizar`    | Carrega a curva e a janela de evolução, gera e imprime a análise determinística. |
| `exportar`     | Exporta evolução da curva, análise e/ou log da aplicação.                        |
| `tesouro`      | Consulta as vendas do Tesouro Direto, com filtros, agregação e `--saida`.         |
| `tesouro-resgates` | Consulta recompras, cupons e vencimentos, com filtros, agregação e `--saida`. |
| `tesouro-estoque` | Consulta o estoque mensal, com filtros por mês, agregação e `--saida`.         |
| `mercado`      | Consulta ou exporta séries de dólar e ouro, com cenário e indicadores.           |
| `reservas`     | Consulta ou exporta as reservas internacionais do BCB, com CSV/JSON e `--saida`. |
| `feriados`     | Lista, consulta ou exporta o calendário de feriados por ano.                     |
| `mcp`          | Inicia o servidor MCP via `stdio`, somente leitura.                              |
| `gui`          | Abre a interface gráfica.                                                        |
| `criar-atalho` | Cria o atalho no desktop e no menu de aplicações.                                |

## Parâmetros comuns

| Parâmetro                     | Comandos                             | Descrição                                        |
| ----------------------------- | ------------------------------------ | ------------------------------------------------ |
| `--data AAAA-MM-DD`           | `consultar`, `atualizar`, `exportar`, `mcp` | Data de referência. Padrão: data local corrente. |
| `--no-cache`                  | `consultar`, `atualizar`, `exportar`, `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Ignora o cache em disco e força uma verificação. |
| `--curva curta\|longa\|ambas` | `consultar`, `exportar`              | Representação da curva.                          |
| `--titulo T`                  | `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Filtro parcial por título, sem caixa/acentos. |
| `--inicio`                    | `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Início inclusivo (data ou mês, conforme o comando). |
| `--fim`                       | `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Fim inclusivo (data ou mês, conforme o comando). |
| `--tipo T`                    | `tesouro-resgates`                   | `recompra`, `cupom` ou `vencimento`.             |
| `--mes AAAA-MM`               | `tesouro-estoque`                    | Seleciona um único mês.                          |
| `--agregar`                   | `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Agrupa os registros conforme o dataset. |
| `--json`                      | `tesouro`, `tesouro-resgates`, `tesouro-estoque` | Emite payload JSON em vez de CSV. |
| `--silencioso`                | `atualizar`                          | Carrega os dados sem imprimir a análise.         |
| `--analise`                   | `exportar`                           | Inclui o texto determinístico da análise.        |
| `--analise-curva curta\|longa` | `exportar`                          | Representação usada na análise (padrão: curta); exige `--analise`. |
| `--atualizar`                 | `mcp`, `feriados`                    | Carrega os dados de hoje ou revalida o calendário antes de responder. |
| `--ano AAAA`                  | `feriados`                           | Ano do calendário (padrão: ano corrente).        |
| `--formato csv\|json`         | `feriados`                           | Formato da listagem/exportação (padrão: csv).    |
| `--log`                       | `exportar`                           | Inclui uma cópia do log ativo.                   |
| `--saida ARQUIVO\|DIRETÓRIO`  | `exportar`, `tesouro`, `tesouro-resgates`, `tesouro-estoque`, `feriados` | Destino da exportação. |
| `--help`                      | todos                                | Exibe a ajuda.                                   |
| `--version`                   | todos                                | Exibe a versão e encerra.                        |

## Regras de data

- O formato é `AAAA-MM-DD`.
- Datas futuras são rejeitadas.
- O histórico disponível cobre os últimos 30 dias.
- Se a data cair em sábado, domingo ou feriado, a CLI usa o dia útil anterior.
- A data é resolvida pela camada de aplicação, com as mesmas regras da GUI.
- O ajuste de data é informado em `stderr`, com a data solicitada, a resolvida
  e o motivo.

## `--curva`

| Comando     | `curta`                                                      | `longa`                                           | `ambas`                  |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------- | ------------------------ |
| `consultar` | Tabela bruta da data (`DU252,DC365,TAXA`)                    | Consolidado por ano (`ANO,MENOR_TAXA,MAIOR_TAXA`) | As duas seções no stdout |
| `exportar`  | Evolução detalhada das cinco datas (`DATA;DU252;DC365;TAXA`) | Evolução consolidada (`DATA;ANO;TAXA_MEDIA`)      | Os dois CSVs             |

No `consultar`, o padrão é `curta`. No `exportar`, `--curva` é opcional e pode
ser combinado com `--analise` e `--log`.

## `consultar`

```bash
b3-selic-pre consultar --data 2026-06-10
b3-selic-pre consultar --data 2026-06-10 --curva longa
b3-selic-pre consultar --data 2026-06-10 --curva ambas
b3-selic-pre consultar --data 2026-06-10 --no-cache
```

Exemplo de saída bruta:

```csv
DU252,DC365,TAXA
1,1,"14,90"
4,6,"14,87"
```

Exemplo de saída consolidada:

```csv
ANO,MENOR_TAXA,MAIOR_TAXA
0,"14,50","15,10"
1,"14,20","14,90"
```

Com `--curva ambas`, cada tabela é precedida por um cabeçalho
(`Curva curta` e `Curva longa`). Para consumo por planilhas, prefira
`exportar`, que gera arquivos separados.

## `atualizar`

```bash
b3-selic-pre atualizar
b3-selic-pre atualizar --data 2026-06-10
b3-selic-pre atualizar --data 2026-06-10 --no-cache
b3-selic-pre atualizar --data 2026-06-10 --silencioso
```

O comando:

1. carrega a curva da data de referência;
2. carrega a janela de evolução de cinco datas (data base e 7, 14, 21 e 28 dias antes);
3. gera o texto determinístico da análise da curva;
4. gera o texto da evolução entre a data base e a data anterior disponível;
5. imprime os dois textos no stdout, salvo com `--silencioso`.

Datas históricas sem dados são omitidas da evolução e listadas no final da
saída como `Datas indisponíveis: ...`.

A análise usa as preferências persistidas de `curva_juros` e `curva_evolucao`,
as mesmas usadas pela GUI.

## `tesouro`

Consulta as vendas do Tesouro Direto publicadas no Tesouro Transparente. O CSV
cumulativo é mantido em `$XDG_CACHE_HOME/b3-selic-pre/tesouro/` e atualizado com
verificação condicional (`ETag`/`Last-Modified`). `304` reutiliza o cache.

```bash
b3-selic-pre tesouro
b3-selic-pre tesouro --titulo Selic --inicio 2026-09-01 --fim 2026-10-14
b3-selic-pre tesouro --agregar
b3-selic-pre tesouro --json
b3-selic-pre tesouro --no-cache
b3-selic-pre tesouro --agregar --saida exports/
```

Regras:

- `--titulo` é parcial e ignora caixa e acentos;
- `--inicio`/`--fim` são inclusivos, no formato `AAAA-MM-DD`, usados exatamente
  como informados (sem ajuste para dia útil);
- sem datas, o período é de 30 dias até a maior `data_liquidacao` disponível;
- `--inicio` maior que `--fim` retorna código `2` sem iniciar download;
- `--agregar` soma quantidade e valor por título e calcula `PU_MEDIO` como
  `valor / quantidade`;
- período vazio produz apenas o cabeçalho CSV (ou lista vazia no JSON), com
  código `0`.

Saídas:

| Formato | Cabeçalho / campos |
| --- | --- |
| CSV | `TIPO_TITULO;VENCIMENTO;DATA_LIQUIDACAO;PU;QUANTIDADE;VALOR` |
| CSV agregado | `TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO` |
| JSON | `fonte`, `origem`, `dataset`, `resource_id`, `data_extracao`, `publicado_em`, `data_maxima_liquidacao`, `total_registros`, `periodo`, `registros` |
| JSON agregado | os mesmos metadados com `agregados` e `total_agregados` no lugar de `registros` |

O CSV usa `;`, datas ISO e ponto decimal. `PU` tem 6 casas; `quantidade` e
`valor` têm 2 casas. No JSON, os valores monetários são strings com ponto
decimal.

Com `--saida`:

- diretório: grava `tesouro-vendas.csv`/`.json`;
- com `--agregar`, usa `tesouro-vendas-agregado.csv`/`.json`;
- arquivo: grava exatamente no caminho informado;
- falha de escrita retorna código `1`.

## `tesouro-resgates`

Consulta recompras, cupons e vencimentos publicados no Tesouro Transparente.
Cada recurso tem CSV e metadata próprios no cache local e é atualizado com
verificação condicional (`ETag`/`Last-Modified`). `304` reutiliza o cache.

```bash
b3-selic-pre tesouro-resgates
b3-selic-pre tesouro-resgates --tipo cupom
b3-selic-pre tesouro-resgates --titulo IPCA --inicio 2026-09-01
b3-selic-pre tesouro-resgates --agregar --json
b3-selic-pre tesouro-resgates --agregar --saida exports/
```

Regras:

- `--tipo` aceita `recompra`, `cupom` ou `vencimento`; omitido, consulta todos;
- `--titulo` é parcial e ignora caixa e acentos;
- `--inicio`/`--fim` são inclusivos em `AAAA-MM-DD`;
- sem datas, o período é de 30 dias até a maior `data_resgate` disponível;
- `--inicio` maior que `--fim` retorna código `2` sem iniciar download;
- recompras não têm `PU`; na agregação, `PU_MEDIO` fica vazio.

Saídas:

| Formato | Cabeçalho |
| --- | --- |
| CSV | `TIPO_RESGATE;TIPO_TITULO;VENCIMENTO;DATA_RESGATE;PU;QUANTIDADE;VALOR` |
| CSV agregado | `TIPO_RESGATE;TIPO_TITULO;QUANTIDADE;VALOR;PU_MEDIO` |
| JSON | `dataset: "resgates"`, período, metadados e `registros` ou `agregados` |

Com `--saida`, usa `tesouro-resgates.csv`/`.json` em diretórios e o sufixo
`-agregado` quando `--agregar` é informado. Falha de escrita retorna código `1`.

## `tesouro-estoque`

Consulta o estoque mensal do Tesouro Direto, que é um snapshot por título.

```bash
b3-selic-pre tesouro-estoque
b3-selic-pre tesouro-estoque --mes 2026-08
b3-selic-pre tesouro-estoque --inicio 2025-01 --fim 2025-12
b3-selic-pre tesouro-estoque --mes 2026-08 --agregar --json
```

Regras:

- sem filtros, usa o último mês disponível;
- `--inicio`/`--fim` usam `AAAA-MM` e são inclusivos;
- `--mes` seleciona um único mês;
- `--agregar` exige um único mês e agrupa por título; somar `valor_estoque`
  entre meses é proibido e retorna código `2`.

Saídas:

| Formato | Cabeçalho |
| --- | --- |
| CSV | `TIPO_TITULO;VENCIMENTO;MES;PU;QUANTIDADE;VALOR_ESTOQUE` |
| CSV agregado | `TIPO_TITULO;QUANTIDADE;VALOR_ESTOQUE;PU_MEDIO` |
| JSON | `dataset: "estoque"`, período, metadados e `registros` ou `agregados` |

Com `--saida`, usa `tesouro-estoque.csv`/`.json` em diretórios e o sufixo
`-agregado` quando `--agregar` é informado. Falha de escrita retorna código `1`.

## `exportar`

Conteúdos combináveis:

```bash
b3-selic-pre exportar --curva curta
b3-selic-pre exportar --curva longa
b3-selic-pre exportar --curva ambas --analise
b3-selic-pre exportar --curva ambas --analise --log --saida exports/
b3-selic-pre exportar --analise
b3-selic-pre exportar --analise --analise-curva longa
b3-selic-pre exportar --log
```

### Formatos

| Conteúdo        | Arquivo padrão     | Formato                                                      |
| --------------- | ------------------ | ------------------------------------------------------------ |
| `--curva curta` | `curva-curta.csv`  | `DATA;DU252;DC365;TAXA`, uma linha por registro por data     |
| `--curva longa` | `curva-longa.csv`  | `DATA;ANO;TAXA_MEDIA`                                        |
| `--analise`     | `analise.txt`      | Texto com as seções `Análise da Curva` e `Evolução da Curva`; com `longa`, usa a taxa média por ano |
| `--log`         | `b3-selic-pre.log` | Cópia do log ativo no momento da exportação                  |

### Destino

- Sem `--saida`, um único artefato é impresso no stdout.
- Com mais de um artefato, `--saida` deve ser um diretório; os arquivos são
  gravados com os nomes da tabela acima.
- Com um único artefato, `--saida` pode ser um arquivo ou um diretório.
- Arquivos existentes com o mesmo nome são sobrescritos.
- O diretório é criado se não existir.

Exemplos:

```bash
# um CSV no terminal
b3-selic-pre exportar --data 2026-06-10 --curva longa

# pacote completo em um diretório
b3-selic-pre exportar --data 2026-06-10 \
  --curva ambas --analise --log --saida /tmp/b3-export
```

O snapshot do log não inclui o registro da própria invocação de `exportar`,
porque esse registro é gravado ao final do processo. Ele contém as invocações
anteriores.


### `--analise-curva`

`--analise-curva curta|longa` seleciona a representação usada no texto da
análise. O padrão é `curta`. A opção exige `--analise` e é independente de
`--curva`:

```bash
# CSV consolidado + análise sobre a taxa média por ano
b3-selic-pre exportar --curva longa --analise --analise-curva longa

# Apenas a análise longa no stdout
b3-selic-pre exportar --analise --analise-curva longa
```

A análise longa usa a mesma base do CSV `DATA;ANO;TAXA_MEDIA` (taxa média por
ano). A tabela de `consultar --curva longa` continua mostrando mínimo e máximo
por ano; são representações diferentes.

## `mcp`

```bash
b3-selic-pre mcp
b3-selic-pre mcp --atualizar
b3-selic-pre mcp --data 2026-06-10
b3-selic-pre mcp --atualizar --data 2026-06-10
```

Inicia o servidor MCP via `stdio`, usando apenas o cache local durante o
atendimento. `--atualizar` carrega a data de hoje antes de atender; `--data`
carrega a data informada. Quando ambos são usados, há uma única carga com a data
informada.

O subcomando não aceita `--no-cache`, `--curva`, `--analise`, `--log` ou
`--saida`. Falhas na preparação encerram com código diferente de zero e o
servidor não inicia. Em `EOF`, o servidor encerra com `0`.

Consulte [Servidor MCP](mcp.md) para o protocolo, as tools, os erros e a
execução em Docker.

## Logging

A CLI reutiliza o mesmo arquivo, formato e rotação diária da aplicação. O
diretório padrão é o cache da plataforma:

```text
<XDG_CACHE_HOME>/b3-selic-pre/logs/b3-selic-pre.log
```

Em Linux sem `XDG_CACHE_HOME`, o caminho é
`~/.cache/b3-selic-pre/logs/b3-selic-pre.log`.

Cada invocação gera uma linha INFO com:

```text
CLI comando=consultar argumentos=data=2026-06-10 curva=longa \
    inicio=2026-10-20T10:00:00-03:00 fim=2026-10-20T10:00:01-03:00 \
    duracao=0.842s codigo_saida=0
```

Campos:

| Campo            | Descrição                                                                   |
| ---------------- | --------------------------------------------------------------------------- |
| `comando`        | Subcomando acionado; `gui` para execução sem argumentos ou `gui`.           |
| `argumentos`     | Argumentos reconhecidos em `chave=valor`; em erro de parsing, o argv bruto. |
| `inicio` / `fim` | Instantes em ISO 8601 com fuso local.                                       |
| `duracao`        | Duração em segundos.                                                        |
| `codigo_saida`   | Código de retorno da invocação.                                             |

Invocações `--help`, `--version`, erros de parsing, falhas de comunicação e
exceções não tratadas também geram o registro. A retenção de backups usa a
configuração `log_retention_days` (padrão: 7 dias), a mesma da GUI.

No modo `mcp`, logs e diagnósticos vão para `stderr` e o arquivo de log ativo
não é gravado.

## Códigos de retorno

| Código | Significado                                                     |
| ------ | --------------------------------------------------------------- |
| `0`    | Sucesso, incluindo `--help`, `--version` e EOF do servidor MCP. |
| `1`    | Falha de comunicação, preparação do MCP ou ausência de dados.   |
| `2`    | Erro de uso, sintaxe inválida ou validação de data/parâmetros.  |

## `mercado`

```bash
b3-selic-pre mercado
b3-selic-pre mercado --ativo ouro --inicio 2026-01-01 --fim 2026-12-31
b3-selic-pre mercado --resolucao mes --formato json
b3-selic-pre mercado --prever --saida exports/
b3-selic-pre mercado --atualizar --formato json
```

Sem `--atualizar` e sem `--no-cache`, o comando lê apenas o cache local e não
acessa a rede. A janela padrão cobre os 12 meses anteriores à maior data
disponível. A resolução `auto` usa pontos diários nos últimos 14 dias, semanais
até 3 meses e mensais acima disso, sempre preservando mínimos e máximos.

O histórico CSV usa `;`, datas ISO e as colunas
`DATA;ATIVO;VALOR;UNIDADE;ORIGEM;METODO`. O cenário CSV usa
`DATA;ATIVO;CENARIO;INFERIOR_80;SUPERIOR_80;INFERIOR_95;SUPERIOR_95;METODO`.
O JSON contém `janela`, `series`, `previsao`, `indicadores`, `origem`,
`gerado_em` e o aviso de que o cenário não é recomendação.

`--prever` com CSV gera dois artefatos: `mercado-historico.csv` e
`mercado-previsao.csv`. Nesse caso `--saida` deve ser um diretório. Com
`--formato json` há um único `mercado.json`. Sem `--saida`, um único artefato é
impresso no stdout.

Códigos de retorno: `0` em sucesso, `1` quando não há dados para a janela ou a
escrita falha, e `2` para datas inválidas, `--inicio` posterior a `--fim` ou
múltiplos artefatos sem diretório de destino.

## `feriados`

Lista, consulta ou exporta o calendário de feriados alimentado pela ANBIMA.

```bash
b3-selic-pre feriados
b3-selic-pre feriados --ano 2026
b3-selic-pre feriados --ano 2026 --formato json
b3-selic-pre feriados --data 2026-04-03
b3-selic-pre feriados --ano 2026 --formato csv --saida feriados.csv
b3-selic-pre feriados --ano 2026 --atualizar
```

Sem `--atualizar`, a listagem e a exportação leem apenas o cache local. Quando
o ano não está em cache, o comando orienta o uso de `--atualizar`. O CSV usa
`;` e as colunas `DATA;DIA_SEMANA;NOME;ORIGEM`; o JSON contém `ano`, `origem`,
`extraido_em` e `feriados`. A consulta de uma data informa se ela é dia útil,
o motivo do ajuste e o nome do feriado.

Códigos de retorno: `0` em sucesso, `1` sem dados para o ano e `2` para
argumentos inválidos ou `--ano` combinado com `--data`.

## `reservas`

Consulta a série diária de reservas internacionais do BCB SGS 13621 (conceito
de liquidez, em US$ milhões).

```bash
b3-selic-pre reservas
b3-selic-pre reservas --janela 3a
b3-selic-pre reservas --inicio 2026-01-01 --fim 2026-10-30
b3-selic-pre reservas --formato json --indicadores
b3-selic-pre reservas --saida exports/
b3-selic-pre reservas --atualizar
```

Sem `--atualizar` e sem `--no-cache`, o comando lê apenas o cache local e não
acessa a rede. A janela padrão cobre os 12 meses anteriores à maior data em
cache; `--janela 3a` cobre até 36 meses. `--no-cache` recarrega a janela retida
de três anos antes de emitir a saída.

O CSV de série usa `;`, datas ISO, ponto decimal e as colunas
`DATA;VALOR;UNIDADE;ORIGEM;METODO`. O JSON contém `janela`, `serie`,
`indicadores`, `origem` e `gerado_em`; `--indicadores` mantém os indicadores no
payload. Os nomes padrão em diretório são `reservas-serie.csv` e
`reservas.json`.

Códigos de retorno: `0` em sucesso, `1` quando não há dados para a janela ou a
escrita falha, e `2` para datas inválidas ou `--inicio` posterior a `--fim`.
