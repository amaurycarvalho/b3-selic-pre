"""Texto orientativo da sub-aba Dólar e Ouro."""

from __future__ import annotations

from typing import Any

Widget = Any
TkModule = Any

ORIENTATION_SECTIONS = (
    (
        "Objetivo",
        (
            "Acompanhar a evolução do dólar e do ouro e comparar o "
            "histórico com o cenário de 12 meses e os sinais de política "
            "cambial."
        ),
    ),
    (
        "Responde a pergunta",
        (
            "O câmbio e o ouro estão em trajetória de alta, estabilidade ou "
            "deterioração, e o mercado espera mudança de direção?"
        ),
    ),
    (
        "Indicadores envolvidos",
        (
            "Dólar em BRL/USD pela série oficial do BCB SGS 1. Ouro em "
            "R$/g derivado de XAU/USD x USD/BRL / 31,1034768. Cenário do "
            "dólar ancorado no Focus e projeção estatística do ouro com "
            "bandas de 80% e 95%. Sinais: prêmio a termo, prêmio DOL, gap "
            "Focus, volatilidade 30/90 dias e regime."
        ),
    ),
    (
        "Como interpretar",
        (
            "A linha mostra o histórico e a faixa mín-máx resume a "
            "amplitude por período. A região sombreada é o futuro, com o "
            "cenário em linha tracejada e as bandas como incerteza, não "
            "como garantia. O ouro é derivado, não é preço oficial da B3. "
            "Base 100 facilita comparar a variação relativa entre os dois "
            "ativos; Fibonacci é apenas um overlay de níveis de preço."
        ),
    ),
)


def build_market_orientation(
    parent: Widget, tk: TkModule, ttk: TkModule
) -> Widget:
    """Build a read-only text box describing the Dólar e Ouro sub-tab."""
    frame = ttk.Frame(parent, padding=(8, 6))
    text = tk.Text(
        frame,
        wrap=tk.WORD,
        width=36,
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


__all__ = ["ORIENTATION_SECTIONS", "build_market_orientation"]
