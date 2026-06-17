## Why

O gráfico atual (curva única para uma data) não permite visualizar como a curva de juros SELIC Pré se movimentou ao longo do tempo. Para análise de tendências, é necessário comparar a curva atual com curvas históricas (7, 14, 21, 28 dias atrás) em um único gráfico, com flechas indicando a direção e magnitude das mudanças em vencimentos-chave.

## What Changes

- Adicionar modo de visualização "Evolução da Curva" na GUI do desktop
- Nova função `fetch_rates_download` para buscar taxas de datas históricas usando o endpoint `GetDownloadFile` da B3
- Nova função `fetch_historical_rates` para buscar taxas de 5 datas (base, 7, 14, 21, 28 dias atrás) em paralelo
- Nova função `average_rate_by_year` para calcular a média entre menor e maior taxa por ano
- Nova função de renderização `render_curve_evolution` com 5 curvas superpostas (gradiente + alpha) e flechas quiver em anos-chave
- Substituir checkbox "Consolidar por ano" por radio buttons com 3 opções: "Detalhado", "Consolidado", "Evolução da Curva"
- Adicionar DatePicker popup calendar para entrada de data visual
- Limite de 30 dias corridos para consultas nos modos Detalhado e Consolidado
- Reposicionar título do gráfico para `y=0.92` (evita sobreposição com toolbar)
- Indicador de progresso durante a busca multi-data
- A opção "Copiar dados" no modo Evolução exporta dados completos das 5 datas
- Bump de versão: `__version__` passa de `"0.2.3"` para `"0.3.0"`

## Capabilities

### New Capabilities
- `curve-evolution`: Gráfico de evolução da curva de juros com 5 datas históricas (7, 14, 21, 28 dias atrás + base), curvas superpostas com gradiente de cor, e flechas quiver nos anos-chave

### Modified Capabilities
- `desktop-rate-browser`: Substituir checkbox por radio buttons (Detalhado/Consolidado/Evolução), adicionar DatePicker calendar, adicionar validação de 30 dias, adicionar indicador de progresso para fetch multi-data, reposicionar título do gráfico
- `data-export`: Copiar dados das 5 datas no modo evolução (formato consolidado expandido)
- `yearly-consolidation`: Adicionar suporte para cálculo da taxa média (avg_rate) entre min_rate e max_rate

## Impact

- `b3_selic_pre.py`: Novas funções de busca multi-data (`fetch_rates_download`, `fetch_historical_rates`), processamento e renderização; alteração de UI (checkbox → radio buttons, DatePicker, validação 30 dias, título y=0.92)
- `__version__`: bump de `"0.2.3"` para `"0.3.0"`
- Dependências: matplotlib (já existente) — quiver já está disponível; sem novas dependências
- Performance: busca de 5 datas (vs 1) pode aumentar tempo de resposta para 5-15s na primeira carga; mitigado com 4 workers paralelos e indicador de progresso
