## 1. Renomear radio buttons e títulos de gráfico

- [x] 1.1 Alterar título da janela em `gui.py:88` de `"B3 SELIC Pré v{version}"` para `"Taxas Referenciais SELIC (B3) v{version}"`
- [x] 1.2 Alterar radio button "Detalhado" (`gui.py:172`) para "Curva curta"
- [x] 1.3 Alterar radio button "Consolidado" (`gui.py:177`) para "Curva longa"
- [x] 1.4 Alterar título placeholder inicial (`gui.py:207`) de `"B3 SELIC Pré"` para `"Curva Curta (SELIC Pré)"`
- [x] 1.5 Alterar títulos do gráfico sem evolução: `"B3 SELIC Pré"` → `"Curva Curta (SELIC Pré)"` e `"B3 SELIC Pré — Consolidado"` → `"Curva Longa (SELIC Pré)"` em `gui.py:442-447`
- [x] 1.6 Alterar títulos do gráfico de evolução 2D: `"B3 SELIC Pré — Evolução Detalhada"` → `"Evolução da Curva Curta (SELIC Pré)"` e `"B3 SELIC Pré — Evolução Consolidada"` → `"Evolução da Curva Longa (SELIC Pré)"` em `gui.py:434-439`
- [x] 1.7 Alterar títulos do gráfico de evolução 3D: `"B3 SELIC Pré — Evolução 3D Detalhada"` → `"Evolução 3D da Curva Curta (SELIC Pré)"` e `"B3 SELIC Pré — Evolução 3D Consolidada"` → `"Evolução 3D da Curva Longa (SELIC Pré)"` em `gui.py:429-430`

## 2. Centralizar título 3D horizontalmente

- [x] 2.1 Remover o bloco de pós-processamento que desloca o título 3D para a esquerda (`gui.py:448-458`), mantendo apenas o `ha="center"` já definido na linha 430

## 3. Bump de versão para 0.9.1

- [x] 3.1 Atualizar `__init__.py:1` de `"0.9.0"` para `"0.9.1"`
- [x] 3.2 Atualizar `pyproject.toml:7` de `"0.8.0"` para `"0.9.1"` (corrige versão defasada)
- [x] 3.3 Atualizar `b3-selic-pre.spec` (linhas 74-75) – `CFBundleShortVersionString` e `CFBundleVersion` para `'0.9.1'`
- [x] 3.4 Adicionar entry no `CHANGELOG.md` para v0.9.1 com as mudanças realizadas
