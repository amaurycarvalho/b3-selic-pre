# PRD — b3-selic-pre

## Propósito

Aplicativo desktop (e CLI) para consultar e visualizar a **curva de juros (taxa referencial SELIC Pré)** divulgada pela B3.

## Problema

Profissionais do mercado financeiro brasileiro precisam acompanhar diariamente a estrutura a termo da taxa SELIC (curva Pré). A B3 disponibiliza os dados via portal web, mas não há uma ferramenta dedicada, leve e offline-friendly para consultar, analisar e visualizar evolutivamente essa curva.

## Público-alvo

- Analistas e gestores de renda fixa
- Economistas e pesquisadores
- Operadores do mercado de derivativos
- Público em geral

## Funcionalidades

| Prioridade | Funcionalidade          | Descrição                                                                                                          |
| ---------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| P0         | Consultar taxa por data | Obter a curva SELIC Pré de uma data específica via CLI ou GUI.                                                     |
| P0         | Visualização gráfica    | Gráfico de linhas (dias corridos vs taxa) com curva detalhada e consolidada por ano.                               |
| P0         | Cache em disco          | Dados armazenados em `~/.cache/b3-selic-pre/` com TTL de 30 min para hoje e retenção infinita para datas passadas. |
| P1         | Evolução histórica      | Sobreposição de curvas dos últimos 28, 21, 14, 7 e 0 dias com setas (quiver).                                      |
| P1         | Painel de análise       | Resumo executivo em linguagem natural com classificação de patamar, inclinação, prêmio de risco e estabilidade.    |
| P1         | Visão 3D                | Superfície 3D da evolução histórica da curva.                                                                      |
| P2         | Exportação CSV          | Copiar dados e imagem do gráfico para a área de transferência.                                                     |
| P2         | Evolução do resumo      | Painel comparativo entre curva atual e anterior com classificação de regime (Bear/Bull/ Twist/Estável).            |
| P2         | Atalho no desktop       | Instalação de atalho no menu de aplicações do sistema.                                                             |

## Métricas de sucesso

- Abertura e consulta de uma data em < 2s (com cache quente)
- Zero dependência de serviços externos além da API da B3
- Binário único autossuficiente (PyInstaller) para as 3 plataformas

## Não-escopo (v1)

- Não é um sistema de trading ou análise em tempo real
- Não substitui sistemas profissionais de risco
- Tesouro Direto (proposto no RFC-001, fora do escopo atual)
