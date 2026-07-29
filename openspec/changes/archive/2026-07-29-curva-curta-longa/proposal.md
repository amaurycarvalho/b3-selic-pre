## Why

Os nomes atuais dos modos de visualização ("Detalhado", "Consolidado") e títulos da aplicação e gráficos não refletem com clareza o que cada modo representa para o usuário final. A mudança para "Curva curta" e "Curva longa" torna a terminologia mais intuitiva (baseada no prazo da curva de juros), e o título da aplicação "Taxas Referenciais SELIC (B3)" é mais descritivo e alinhado ao nome do ativo. A release 0.9.1 incorpora esses ajustes de nomenclatura.

## What Changes

- Título da janela: `"B3 SELIC Pré v{version}"` → `"Taxas Referenciais SELIC (B3) v{version}"`
- RadioButton "Detalhado" → "Curva curta"
- RadioButton "Consolidado" → "Curva longa"
- Títulos dos gráficos atualizados para refletir a nova nomenclatura ("Curva Curta" / "Curva Longa")
- Título 3D centralizado horizontalmente (remoção do deslocamento artificial via `set_x`)
- Versão bumpada de 0.9.0 → 0.9.1

## Capabilities

### New Capabilities
*(Nenhuma — trata-se apenas de renomeação e ajuste de UI)*

### Modified Capabilities
- `window-title`: Título base da aplicação muda de "B3 SELIC Pré" para "Taxas Referenciais SELIC (B3)" nos cenários especificados
- `yearly-consolidation`: Rótulos dos radio buttons mudam de "Detalhado"/"Consolidado" para "Curva curta"/"Curva longa"
- `curve-evolution-detailed`: Referência ao radio button "Detalhado" substituída por "Curva curta"
- `curve-evolution`: Referências aos radio buttons "Detalhado" e "Consolidado" substituídas por "Curva curta" e "Curva longa"
- `curve-evolution-3d`: Comportamento de centralização do título 3D alterado — título deve ser centralizado horizontalmente, não mais deslocado à esquerda

## Impact

- `src/b3_selic_pre/presentation/gui.py`: ~11 pontos de alteração (título janela, labels, títulos de gráfico, centralização 3D)
- `src/b3_selic_pre/__init__.py`: version bump 0.9.0 → 0.9.1
- `pyproject.toml`: version bump 0.8.0 → 0.9.1 (corrige defasagem)
- `b3-selic-pre.spec`: version bump 0.9.0 → 0.9.1
- `CHANGELOG.md`: adicionar entry v0.9.1
- `openspec/specs/`: 5 specs modificadas (conteúdo textual, sem alteração de contratos de API)
