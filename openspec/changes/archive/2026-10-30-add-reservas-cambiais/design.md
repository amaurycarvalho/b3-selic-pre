# Design

## Context

Ver `proposal.md` para motivação e `specs/` para o contrato de comportamento.

Esta change depende de `add-cambio-ouro-forecast` implementado e arquivado antes. Ela reutiliza o núcleo de mercado que aquela change cria:

- `BcbSgsClient` em `infrastructure/market/bcb_client.py`.
- `SourceRef`, `MarketSeries`, `Bucket` e `Resolution` em `domain/market.py`.
- Cache bruto, cache derivado e pré-cálculo por hash em `infrastructure/market/`.
- Housekeeping de 3 anos e lock dedicado de mercado.
- Helpers de exportação e as regras de `--saida` em `application/market/export.py` e `presentation/cli_*`.
- Padrão de sub-notebook lazy e de views headless.

A aba `Câmbio e Ouro` já nasce como sub-notebook por causa desta change (ajuste registrado em `add-cambio-ouro-forecast/design.md`). A sub-aba `Reservas Internacionais` entra como segunda sub-aba.

Spike da fonte (fonte da verdade para este desenho):

- SGS 13621 é diária, em US$ milhões, conceito de liquidez, com ~960 pontos em ~3,8 anos e ~37 KB de JSON.
- SGS 13982 é o conceito de caixa e tem valores diferentes; SGS 3546 é mensal.
- A API do BCB não pede chave, aceita intervalo e `ultimos/N?formato=json`, e devolve `[{"data":"dd/mm/aaaa","valor":"<string>"}]`.
- O volume é pequeno; o problema real é invalidação de cache e definição do sinal, não tamanho de payload.

Restrições de projeto:

- `application` não importa `presentation`, Tkinter, matplotlib nem clientes de rede.
- Testes de UI não podem aumentar o orçamento; a lógica nova é headless.
- `make lint` e `make complexity` exigem módulos pequenos e complexidade controlada.
- O cache vive sob o diretório XDG já usado pela aplicação.

## Goals / Non-Goals

**Goals:**

- Entregar uma camada headless de série, cache, pré-cálculo e indicadores de reservas, compartilhada por GUI, CLI e MCP.
- Manter a primeira exibição da sub-aba instantânea, lendo apenas cache e artefato pré-calculado.
- Invalidar o pré-cálculo somente quando a matriz de origem ou os parâmetros mudarem.
- Manter o cache de reservas limitado a 3 anos.
- Tornar o sinal de deterioração determinístico, testável e explícito como direcional.

**Non-Goals:**

- Recomendação de investimento, previsão de nível futuro ou causalidade macroeconômica.
- Decomposição das reservas por componente (ouro, SDR, posição no FMI, moedas).
- Cobertura de importações, dívida externa ou adequação de reservas.
- Dados intradiários ou streaming.
- Alterar o comportamento de dólar e ouro do `add-cambio-ouro-forecast`.

## Decisions

### 1. Sub-aba dentro de `Câmbio e Ouro`, com `Atualizar` próprio

```
[ SELIC Pre ] [ Tesouro Direto ] [ Cambio e Ouro ] [ Sobre ]
                                   |
                                   +-- [ Dolar e Ouro ]
                                   +-- [ Reservas Internacionais ]  <- nova
```

A sub-aba `Reservas Internacionais` é registrada no sub-notebook lazy de `Câmbio e Ouro`, depois de `Dólar e Ouro`. O `Atualizar` fica dentro da sub-aba e busca apenas a série de reservas, no mesmo padrão por sub-aba adotado pelo Tesouro. Falha do Yahoo ou do Focus não atrasa nem bloqueia reservas.

Alternativa descartada: acrescentar reservas ao `Atualizar` da sub-aba `Dólar e Ouro`; acoplaria uma fonte barata e estável a uma fonte não oficial com rate limit.

### 2. Série oficial única e janela

Fonte: **BCB SGS 13621**, diária, conceito de liquidez, em US$ milhões.

- Cache: retenção de 3 anos.
- Exibição: janela padrão de 12 meses; opção de 3 anos.
- Apresentação: US$ bilhões (`valor_milhoes / 1000`), com o valor bruto preservado no payload.
- Sem interpolação silenciosa: fins de semana e feriados simplesmente não têm ponto.

Alternativas descartadas: 13982 (conceito de caixa, outro contrato) e 3546 (mensal, perde resolução para detectar deterioração).

### 3. Snapshot normalizado + hash canônico, em vez de um arquivo por data

O cache bruto de mercado aceita dois formatos: partições por data e **snapshot normalizado por fonte**. Reservas usa o segundo:

```json
{
  "schema_version": 1,
  "source": "BCB SGS 13621",
  "unit": "USD_milhoes",
  "method": "oficial",
  "extracted_at": "...",
  "points": [{"date": "2026-10-28", "value": 364540.0}]
}
```

O hash do snapshot é calculado sobre os pares `(data, valor)` canônicos, não sobre os bytes do arquivo. Assim, regravar o snapshot com outro `extracted_at` não dispara o pré-cálculo. Um arquivo por data seria viável (≈960 arquivos), mas o snapshot é mais simples e evita custo de metadados sem ganho real para ~37 KB.

A extensão é registrada no delta de `market-data-cache`. Ela não altera o formato usado por dólar e ouro.

### 4. Busca incremental com sobreposição para revisões

A fonte aceita intervalo. A atualização busca a partir da última data em cache, recuando uma sobreposição configurável (default: 5 dias úteis) para capturar revisões de valores recentes. O snapshot é mesclado por data; valores revisados substituem os antigos.

- Atualização forçada (`--no-cache`) recarrega a janela retida.
- Falha de rede mantém o snapshot anterior e é registrada no status.
- O snapshot só é regravado quando o conjunto normalizado muda; a escrita é atômica.

### 5. TTL por recência

```
ultimo dia util      15-30 min
mes corrente         1-6 h
> 1 mes              imutavel
pre-calculado        por hash
```

O TTL não impede a leitura do artefato pré-calculado; ele decide quando o cache bruto precisa ser revalidado em operações que permitem rede.

### 6. Pré-cálculo e hash da janela retida

O `Atualizar` grava o snapshot e chama o pré-cálculo. O hash é:

```
sha256(
  schema_version + fonte + unidade +
  pares (data, valor) canonicos da janela retida +
  parametros de indicadores e regime
)
```

A janela retida é `max_data - 3 anos`. O hash **não** inclui datas fora da retenção, para que o housekeeping não invalide o artefato.

Artefato:

```
precomputed/reservas/<hash>/artifact.json
{
  schema_version, hash, latest_data_date, generated_at,
  source, unit, window_retained,
  series: buckets (dia/semana/mes),
  indicators: {...},
  regime: "aumento" | "estavel" | "deterioracao",
  thresholds: {...},
  provenance: {...}
}
```

- Escrita atômica e lock compartilhado de mercado.
- Se o hash não mudou, o pré-cálculo retorna sem recalcular.
- Falha preserva o artefato anterior; a sub-aba mostra o último artefato válido com aviso de defasagem.

Os indicadores são calculados sobre a série **diária** antes do bucketing, para não distorcer variações e drawdown.

### 7. Indicadores e regime determinístico

```
nivel_atual        ultimo valor em US$ bi
var_1m/3m/12m      (P_t / P_{t-k} - 1) * 100
tendencia_90d      OLS(log P) * 252, anualizada
drawdown_12m       (P_t / max(P, 12m) - 1) * 100
posicao_faixa_12m  (P_t - min12m) / (max12m - min12m)
regime             regra deterministica
```

Default configurável:

```
aumento       var_3m > +2%  e  P_t >= media_90d
deterioracao  var_3m < -2%  e  drawdown_12m <= -3%
estavel       caso contrario
```

- `tendencia_90d` usa regressão linear sobre o log do nível.
- `var_*` usa o ponto disponível mais próximo da data-alvo, nunca interpolação.
- Métricas sem histórico suficiente são omitidas individualmente.
- O regime é rotulado como sinal direcional, não como recomendação.

Alternativas descartadas: change-point estatístico, Bayesian structural break e decomposição por componente. Ficam para uma change futura, depois de acumular histórico e dados auxiliares.

### 8. Bucketing reutilizado

A série usa o mesmo bucketing em camadas do mercado:

```
|-- mensal (> 3m) --|-- semanal (15d..3m) --|-- diario (<= 14d) --| hoje
```

Cada bucket preserva mínimo, máximo e último. O gráfico usa o último valor para a linha e, opcionalmente, a faixa mín-máx. O eixo x é tempo real, não índice. A resolução não altera os indicadores, que usam a série diária.

Alternativa descartada: bucket próprio para reservas; duplicaria código sem ganho.

### 9. Gráfico

- Um painel principal de linha/área em US$ bilhões.
- Seletor de janela `12m | 3a`.
- Médias móveis de 30 e 90 dias.
- Marcadores de máximo e mínimo da janela.
- Selo de regime e dos limiares usados.
- Aviso de defasagem quando `latest_data_date` estiver atrás do último dia útil esperado.
- Estado vazio orientando o `Atualizar`.

O renderizador só desenha; série, buckets, indicadores e textos vêm de view-model headless.

### 10. Fronteiras de módulo

| Camada | Módulos novos |
|---|---|
| `domain` | `reserves.py`: `ReservesIndicators`, `ReservesRegime`, `ReservesThresholds` |
| `application` | `reserves/series.py`, `reserves/indicators.py`, `reserves/payloads.py`, `reserves/config.py`, `reserves/export.py` |
| `infrastructure` | reuso de `market/`; composição em `reserves/` e adaptação do snapshot no cache de mercado |
| `presentation` | `reserves_view_model.py`, `reserves_chart_data.py`, `charts_reserves.py`, `gui/reserves_sub_tab.py`, handler CLI, handlers MCP e catálogo |

`application` recebe adaptadores por protocolo; `infrastructure` não importa `presentation`; GUI e CLI montam os adaptadores no composition root.

### 11. CLI e MCP

CLI:

```
b3-selic-pre reservas
  --inicio AAAA-MM-DD  --fim AAAA-MM-DD
  --janela 12m|3a      --formato csv|json
  --saida CAMINHO      --no-cache  --atualizar
```

- CSV de série: `DATA;VALOR;UNIDADE;ORIGEM;METODO`, com `;` e datas ISO.
- JSON: `janela`, `serie`, `indicadores`, `origem`, `gerado_em`.
- Sem `--atualizar` e sem `--no-cache`, não acessa a rede.
- Regras de `--saida` e nomes padrão seguem o `exportar`: `reservas-serie.csv` e `reservas.json`.

MCP:

- `reservas_serie` (filtros de janela, paginação).
- `reservas_indicadores` (nível, variações, tendência, drawdown, posição, regime e limiares).
- `reservas_exportar` (CSV/JSON, sem gravar arquivo).

Todas somente leitura, alimentadas apenas por cache/artefato pré-calculado, com erro de domínio `sem_dados`.

### 12. Datas, unidades e normalização

- Datas do BCB vêm em `dd/mm/aaaa`; o adaptador normaliza para ISO antes do cache.
- Valores vêm como string em US$ milhões; o adaptador converte para `float` e preserva a unidade.
- A apresentação converte para US$ bilhões; a exportação CSV usa US$ milhões.
- O calendário de referência é `America/Sao_Paulo`.
- Fins de semana e feriados não são preenchidos; a lacuna é explícita.

### 13. Configuração

Limiares de regime, janela padrão, sobreposição de revisão, TTLs e retenção ficam em `application/reserves/config.py`, construídos a partir de mapping, sem importar `Settings`. A presentation monta a configuração e a injeta, seguindo o padrão de `CurvaJurosConfig`.

### 14. Texto orientativo e hover da sub-aba

A sub-aba `Reservas Internacionais` replica o padrão de orientação de
`Dólar e Ouro`: um `Text` somente leitura ao lado do gráfico, com as seções
`Objetivo`, `Responde a pergunta`, `Indicadores envolvidos` e
`Como interpretar`. O texto cobre BCB SGS 13621, conversão para US$ bilhões,
variações, tendência, drawdown, posição na faixa, regime, médias móveis,
janelas e defasagem.

Decisões de layout:

- O painel orientativo ocupa 20% da largura útil (`weight=1` contra
  `weight=4` do gráfico). Em `Dólar e Ouro`, a divisão é 3:1 (25%).
- A largura solicitada do `Text` cai de 36 para 29 colunas, também 20% menor,
  para que a redução não dependa apenas da distribuição do `PanedWindow`.
- O texto continua somente leitura, com rolagem vertical e quebra de palavra.

Cada ponto histórico do gráfico registra um `HoverPoint` com data, valor em US$
bilhões, médias móveis de 30 e 90 dias e indicação de máximo/mínimo da janela.
O hover usa a mesma infraestrutura dos gráficos de mercado, com distância
máxima de 20 px, e não acessa rede nem recalcula indicadores.

## Risks / Trade-offs

- **Dependência de change ainda não implementada** → implementar `add-cambio-ouro-forecast` primeiro; o delta de `market-data-cache` só arquiva depois que ela existir. O `openspec validate` atual avisa que o arquivamento falharia hoje; isso é esperado e é o mecanismo que força a ordem.
- **Revisões recentes do BCB** → sobreposição de 5 dias úteis; valor revisado substitui o antigo no snapshot.
- **Sinal de deterioração é direcional, não causal** → rótulo explícito; sem afirmar motivo macroeconômico.
- **Limiares arbitrários** → default documentado e configurável; testes cobrem os três regimes e a histerese não é usada na v1.
- **Hash e housekeeping acoplados** → hash restrito à janela retida; teste garante que limpeza fora da janela não dispara pré-cálculo.
- **Cache snapshot pode mascarar lacuna** → status e payload expõem `latest_data_date` e datas ausentes; não há preenchimento silencioso.
- **Complexidade/lint** → módulos pequenos por responsabilidade; sem novas dependências.
- **Orçamento de testes de UI** → toda a lógica nova é headless; nenhum teste Tkinter novo.

## Migration Plan

- Change aditiva: nova sub-aba, novo subcomando e novas tools; nada existente é removido ou renomeado.
- O cache de reservas usa o diretório de mercado com namespace próprio; não há migração de cache antigo.
- Rollback: remover o registro da sub-aba, o subcomando e as tools; o namespace de cache de reservas pode ser apagado sem afetar SELIC, Tesouro, dólar ou ouro.
- Ordem de aplicação: arquivar `add-cambio-ouro-forecast` antes desta change.

## Open Questions

- Se uma futura sub-aba deve mostrar a decomposição das reservas por componente. Fora de escopo agora.
- Se o regime deve usar histerese para evitar oscilação perto dos limiares. Só depois de medir a frequência de troca com dados reais.
