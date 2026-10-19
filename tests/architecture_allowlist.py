"""Aprovações explícitas para violações conhecidas de fronteiras de camada.

Cada entrada é uma dívida técnica rastreada. Remover entradas é sempre
permitido; adicionar uma nova entrada exige aprovação explícita em revisão de
código, pois concede uma exceção à regra de dependências da Clean Architecture.

As entradas são verificadas por ``tests/test_architecture.py`` e uma entrada
obsoleta (que não corresponde mais a uma violação real) também faz o teste
falhar, forçando a limpeza após cada refatoração.
"""

LAYER_IMPORTS: dict[tuple[str, str], str] = {
    (
        "b3_selic_pre.presentation.cli",
        "infrastructure",
    ): "Composition root: instancia adapters de infraestrutura e os injeta "
    "nos casos de uso.",
    (
        "b3_selic_pre.presentation.gui.launch",
        "infrastructure",
    ): "Composition root da GUI: monta cliente B3, atalho, ícone e settings "
    "e injeta na janela.",
}

EXTERNAL_IMPORTS: dict[tuple[str, str], str] = {}
