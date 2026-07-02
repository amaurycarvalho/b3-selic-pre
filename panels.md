# b3-selic-pre

Curva de juros (taxa referencial SELIC) conforme a B3.

## Interface gráfica

Dois modos base selecionáveis por radio button, com opção adicional de evolução:

| Modo                    | Descrição                                                                                                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Detalhado**           | Curva completa Dias úteis × taxa (linha verde), com grid trimestral (~66 DU) e ticks finos a cada ~22 DU                                                                                    |
| **Consolidado**         | Envelope anual consolidado (taxa mínima em azul, máxima em vermelho), com grid trienal (3 anos) e ticks finos a cada ano                                                                    |
| **Evolução da curva** ☐ | Checkbox que sobrepõe 5 curvas históricas (hoje, 7, 14, 21, 28 dias atrás) com gradiente de cor e flechas quiver nos ticks secundários (~22 DU / ~1 ano), combinável com qualquer modo base |

Na interface, informe a data no formato `YYYY-MM-DD` e clique em `Buscar`.
Use o botão `📅` ao lado do campo de data para abrir um calendário popup.

**Limite de consulta**: nos modos Detalhado e Consolidado, apenas datas nos últimos 30 dias corridos são aceitas.

**Evolução da curva**: ao marcar o checkbox, a data é automaticamente alterada para a data atual. O sistema busca as 5 curvas (28, 21, 14, 7, 0 dias atrás) em paralelo e as sobrepõe ao gráfico do modo base ativo.

Recursos disponíveis:

- Zoom e pan no gráfico
- Cópia de dados para área de transferência
- Cópia do gráfico como imagem
- Exportação do gráfico em PNG
- Criação de atalho no desktop (botão "Criar Atalho Desktop" ou `--create-shortcut`)

## Indicadores e cálculos envolvidos

## Parametrizações
