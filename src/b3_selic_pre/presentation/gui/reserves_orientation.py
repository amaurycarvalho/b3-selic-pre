"""Texto orientativo da sub-aba Reservas Internacionais."""

from __future__ import annotations

from typing import Any

Widget = Any
TkModule = Any
TEXT_WIDTH = 29

ORIENTATION_SECTIONS = (
    (
        "Objetivo",
        (
            "Acompanhar a evolução do estoque de reservas internacionais "
            "brasileiras em dólares e identificar se o colchão externo está "
            "aumentando, estável ou em deterioração."
        ),
    ),
    (
        "Responde a pergunta",
        (
            "As reservas internacionais estão em trajetória de aumento, "
            "estabilidade ou deterioração no horizonte de 12 meses?"
        ),
    ),
    (
        "Indicadores envolvidos",
        (
            "Série diária oficial BCB SGS 13621, conceito de liquidez, em "
            "US$ milhões e exibida em US$ bilhões. Indicadores: nível atual, "
            "variações de 1, 3 e 12 meses, tendência de 90 dias, drawdown de "
            "12 meses, posição na faixa de 12 meses e regime determinístico."
        ),
    ),
    (
        "Como interpretar",
        (
            "A linha mostra o histórico e a área destaca o nível das reservas. "
            "As linhas tracejadas são as médias móveis de 30 e 90 dias. O "
            "regime é um sinal direcional, não uma recomendação. Janelas de "
            "12 meses e 3 anos mudam apenas o recorte exibido; os indicadores "
            "usam a série diária. Fins de semana e feriados não são "
            "preenchidos. O selo de defasagem alerta quando o último dado "
            "está atrasado em relação ao último dia útil esperado."
        ),
    ),
)


def build_reserves_orientation(
    parent: Widget, tk: TkModule, ttk: TkModule
) -> Widget:
    """Build a read-only text box describing the reserves sub-tab."""
    frame = ttk.Frame(parent, padding=(8, 6))
    text = tk.Text(
        frame,
        wrap=tk.WORD,
        width=TEXT_WIDTH,
        state=tk.DISABLED,
        font=("TkDefaultFont", 9),
        padx=6,
        pady=6,
    )
    text.tag_configure("section", font=("TkDefaultFont", 9, "bold"))
    scrollbar = ttk.Scrollbar(
        frame, orient=tk.VERTICAL, command=text.yview
    )
    text.configure(yscrollcommand=scrollbar.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text.configure(state=tk.NORMAL)
    for index, (title, body) in enumerate(ORIENTATION_SECTIONS):
        if index:
            text.insert(tk.END, "\n\n")
        text.insert(tk.END, f"{title}:", "section")
        text.insert(tk.END, f"\n{body}")
    text.configure(state=tk.DISABLED)
    return frame


__all__ = [
    "ORIENTATION_SECTIONS",
    "TEXT_WIDTH",
    "build_reserves_orientation",
]
