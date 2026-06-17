## Context

`b3_selic_pre.py` não possui nenhuma definição de versão. O título da janela é fixo (`"B3 SELIC Pré"`) e o CLI não aceita `--version`. Com releases versionadas via git tag, não há como o usuário saber qual versão está executando.

## Goals / Non-Goals

**Goals:**
- Definir `__version__` como fonte única da versão no código
- Exibir versão na barra de título da GUI: `"B3 SELIC Pré v<version>"`
- Adicionar flag `--version` no CLI que imprime a versão e sai

**Non-Goals:**
- Automatizar sincronia entre `__version__` e git tags (manual por enquanto)
- Adicionar `pyproject.toml` ou empacotamento pip
- Exibir versão em outros lugares (status bar, about dialog)

## Decisions

### 1. Fonte da versão: `__version__` no próprio script (Opção A)

Uma constante `__version__` no topo de `b3_selic_pre.py`, seguindo PEP 396.

```python
__version__ = "0.2.0"
```

**Alternativas consideradas:**
- `_version.py` separado → arquivo extra sem benefício real para um single-file app
- `pyproject.toml` + `importlib.metadata` → não funciona em binários PyInstaller
- Ler do CHANGELOG.md com regex → frágil e desnecessário

### 2. Uso no título da janela

```python
root.title(f"B3 SELIC Pré v{__version__}")
```

Substitui o título fixo atual na linha 241.

### 3. Flag --version no CLI

Usar `argparse` `action="version"` que já formata a saída automaticamente:

```python
parser.add_argument(
    "--version",
    action="version",
    version=f"b3-selic-pre {__version__}",
)
```

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| **Versão do código dessincronizada do CHANGELOG / git tag** | Checklist de release inclui verificar `__version__`; diferença pequena é aceitável |
| **0.2.0 não reflete o histórico real de mudanças** | Ajustar o número antes de implementar — `0.1.0` se for a primeira release, `0.2.0` se considerar que o app já mudou desde a concepção |
