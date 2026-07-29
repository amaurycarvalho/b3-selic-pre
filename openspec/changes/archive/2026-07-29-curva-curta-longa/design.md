## Context

A aplicação GUI usa `tkinter` com `matplotlib` embutido. Atualmente os rótulos e títulos referenciam "B3 SELIC Pré", "Detalhado" e "Consolidado". A estrutura de código é de arquitetura limpa (`domain → application → infrastructure → presentation`), e todas as strings de UI estão concentradas em `presentation/gui.py` e `infrastructure/desktop.py`. O atalho desktop já usa o nome "Taxas Referenciais SELIC (B3)" — não requer alteração.

## Goals / Non-Goals

**Goals:**
- Renomear título da janela, radio buttons e títulos de todos os gráficos
- Centralizar o título do gráfico 3D horizontalmente
- Bump de versão para 0.9.1 nos arquivos de versão e CHANGELOG

**Non-Goals:**
- Não alterar lógica de negócio, contratos de API, ou estrutura de dados
- Não alterar tooltips, settings, ou chaves internas (`view_mode` continua `raw`/`consolidated`)
- Não alterar o atalho desktop (já está correto)

## Decisions

1. **Substituição direta de strings em `gui.py`**: Como as alterações são puramente cosméticas (rótulos e títulos), basta substituir as strings literais nos ~11 pontos identificados. Não há necessidade de internacionalização ou constantes centralizadas.
2. **Remoção do pós-processamento de título 3D (linhas 448-458)**: O ajuste `t.set_x(0.5 - 0.7 * w_ax)` desloca o título para a esquerda para compensar a colorbar. A nova exigência de centralização horizontal torna esse ajuste desnecessário — `ha="center"` já está definido na linha 430. O bloco inteiro será removido.
3. **Version bump único**: `__init__.py` como fonte da verdade. `pyproject.toml` será corrigido da versão defasada 0.8.0 para 0.9.1. `.spec` acompanha.

## Risks / Trade-offs

- [Baixo] A remoção do ajuste `set_x` pode fazer o título 3D colidir com a colorbar em janelas muito estreitas. Mitigação: `ha="center"` com `y=1.06` já mantém o título acima da área do gráfico; a colorbar fica à direita; o risco de sobreposição é mínimo.
- [Baixo] Os nomes dos radio buttons mudam, mas a chave de configuração (`view_mode`) permanece `"raw"`/`"consolidated"` — usuários com settings salvos não perdem o estado.
