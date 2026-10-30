"""Aba Sobre com o mesmo conteúdo do diálogo de informações."""

from __future__ import annotations

from typing import Any

from b3_selic_pre import __release_date__, __version__
from b3_selic_pre.application.about import AboutInfo, build_about_info
from b3_selic_pre.presentation.gui.about import AboutMixin
from b3_selic_pre.presentation.gui.dependencies import GuiDependencies

Widget = Any
TkModule = Any

ABOUT_SECTIONS = (
    (
        "Aplicação",
        (
            "O b3-selic-pre consulta a curva de juros SELIC Pré da B3 e os "
            "datasets do Tesouro Direto. Oferece interface gráfica, linha de "
            "comando e servidor MCP somente leitura."
        ),
    ),
    (
        "Linha de comando",
        (
            "Sintaxe geral:\n"
            "  b3-selic-pre <comando> [opções]\n\n"
            "Comandos:\n"
            "  consultar --data AAAA-MM-DD --curva curta|longa|ambas\n"
            "    Consulta a curva da data; --curva escolhe a visualização.\n"
            "  atualizar --data AAAA-MM-DD\n"
            "    Carrega a evolução da curva e imprime a análise.\n"
            "  exportar --curva curta|longa|ambas --analise --log --saida DIR\n"
            "    Exporta curvas, análise e/ou log para o diretório indicado.\n"
            "  tesouro --titulo T --inicio AAAA-MM-DD --fim AAAA-MM-DD "
            "--agregar --json --no-cache --saida DIR\n"
            "    Consulta vendas do Tesouro com filtros e exportação.\n"
            "  tesouro-resgates --tipo recompra|cupom|vencimento [filtros]\n"
            "    Consulta recompras, cupons e vencimentos.\n"
            "  tesouro-estoque --mes AAAA-MM [filtros]\n"
            "    Consulta o estoque mensal do Tesouro.\n"
            "  gui\n"
            "    Abre a interface gráfica (padrão sem argumentos).\n"
            "  criar-atalho\n"
            "    Cria o atalho no desktop.\n\n"
            "Parâmetros comuns:\n"
            "  --data AAAA-MM-DD: data de referência da consulta.\n"
            "  --curva curta|longa|ambas: modo de visualização da curva.\n"
            "  --no-cache: ignora o cache local e busca a fonte.\n"
            "  --saida DIR: grava a saída em arquivos no diretório.\n"
            "  --json: emite JSON em vez de CSV nos comandos do Tesouro."
        ),
    ),
    (
        "Servidor MCP",
        (
            "O MCP (Model Context Protocol) é um protocolo para agentes e "
            "ferramentas externas consultarem dados da aplicação via stdio. "
            "O servidor é somente leitura, usa o cache local e não acessa a "
            "rede nem grava estado durante o atendimento.\n\n"
            "Tools disponibilizadas:\n"
            "  data_referencia, consultar_curva, exportar_curva_curta, "
            "exportar_curva_longa, analise, evolucao, estatisticas, "
            "listar_datas, tesouro_vendas, tesouro_resgates e "
            "tesouro_estoque.\n\n"
            "Sintaxe:\n"
            "  b3-selic-pre mcp\n"
            "    Inicia o servidor usando o cache existente.\n"
            "  b3-selic-pre mcp --atualizar\n"
            "    Carrega os dados antes de atender.\n"
            "  b3-selic-pre mcp --data AAAA-MM-DD\n"
            "    Define a data de referência do atendimento."
        ),
    ),
)


class AboutTab(AboutMixin):
    """Reaproveita o conteúdo do diálogo Sobre dentro de uma aba."""

    def __init__(
        self: AboutTab,
        parent: Widget,
        *,
        root: Widget,
        dependencies: GuiDependencies,
    ) -> None:
        """Build the about content into the tab frame."""
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.deps = dependencies
        self._about_dialog = None
        self.frame = parent
        info = build_about_info(__version__, __release_date__)
        outer = ttk.Frame(parent, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        frame = ttk.LabelFrame(
            outer, text="Sobre o b3-selic-pre", padding=12
        )
        frame.pack(fill=tk.BOTH, expand=True)
        self._build_about_header(frame, frame, info, tk, ttk)
        ttk.Label(
            frame, text=info.description, wraplength=720, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(12, 0))
        self._build_tab_actions(frame, frame, info, tk, ttk)
        self._build_orientation_panel(frame, tk, ttk)
        footer = ttk.Frame(frame)
        footer.pack(fill=tk.X, pady=(12, 0))
        frame._about_footer = footer
        frame._about_message = ttk.Label(
            footer, text="", foreground="orange"
        )
        frame._about_message.pack(anchor=tk.W)
        self._host = frame
        self._start_version_check(frame)

    def _build_tab_actions(
        self: AboutTab,
        frame: Widget,
        host: Widget,
        info: AboutInfo,
        tk: TkModule,
        ttk: TkModule,
    ) -> None:
        """Render the repository and log directory buttons."""
        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(
            actions,
            text="Repositório",
            command=lambda: self._open_about_url(
                host, info.repository_url
            ),
        ).pack(side=tk.LEFT)
        ttk.Button(
            actions,
            text="Diretório de logs",
            command=lambda: self._open_about_logs(host),
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _build_orientation_panel(
        self: AboutTab,
        parent: Widget,
        tk: TkModule,
        ttk: TkModule,
    ) -> None:
        """Render a read-only summary of the app, CLI and MCP server."""
        panel = ttk.LabelFrame(
            parent,
            text="Aplicação, CLI e servidor MCP",
            padding=(8, 6),
        )
        panel.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        text = tk.Text(
            panel,
            wrap=tk.WORD,
            height=14,
            state=tk.DISABLED,
            font=("TkDefaultFont", 9),
            padx=6,
            pady=6,
        )
        text.tag_configure("section", font=("TkDefaultFont", 9, "bold"))
        scrollbar = ttk.Scrollbar(
            panel, orient=tk.VERTICAL, command=text.yview
        )
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(state=tk.NORMAL)
        for index, (title, body) in enumerate(ABOUT_SECTIONS):
            if index:
                text.insert(tk.END, "\n\n")
            text.insert(tk.END, f"{title}:", "section")
            text.insert(tk.END, f"\n{body}")
        text.configure(state=tk.DISABLED)

    def close(self: AboutTab) -> None:
        """Nothing to release; the tab host owns the widgets."""
        return
