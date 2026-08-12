"""Helpers e funções de renderização de gráficos de taxas SELIC e pré-fixadas.

Este módulo concentra toda a lógica de desenho dos gráficos exibidos na
interface: o gráfico principal da curva, a evolução da curva ao longo das
datas e a visualização tridimensional. Cada função recebe a figura matplotlib
e os registros, e configura eixos, linhas, marcações e rótulos diretamente.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from b3_selic_pre.application.use_cases import average_rate_by_year
from b3_selic_pre.domain.models import RateRecord

if TYPE_CHECKING:
    import numpy as np
    from matplotlib.axes import Axes
    from matplotlib.colors import Colormap
    from matplotlib.figure import Figure


def _nearest_ticks(
    all_values: list[int], targets: range, tolerance: int, exclude_set: set[int] | None = None
) -> list[int]:
    """Seleciona, entre os valores disponíveis, os mais próximos dos alvos.

    Para cada alvo em ``targets``, procura o valor de ``all_values`` mais
    próximo dentro de ``tolerance``. Valores já escolhidos em iterações
    anteriores são pulados para evitar marcações duplicadas no eixo.
    """
    result = []
    seen = set(exclude_set) if exclude_set else set()
    for target in targets:
        nearest = min(all_values, key=lambda d: abs(d - target))
        if abs(nearest - target) <= tolerance and nearest not in seen:
            result.append(nearest)
            seen.add(nearest)
    return result


def _interpolate_rates(records: list[RateRecord], common_x: np.ndarray) -> np.ndarray:
    """Interpola as taxas dos registros na grade comum de dias úteis.

    Registros ausentes fora do intervalo coberto retornam ``NaN``, o que
    permite combinar curvas de datas diferentes com comprimentos distintos.
    """
    import numpy as np
    days = [r.day252 for r in records]
    rates = [float(r.rate.replace(",", ".")) for r in records]
    return np.interp(common_x, days, rates, left=np.nan, right=np.nan)


def _render_empty(fig: Figure, message: str, xlabel: str, ylabel: str) -> None:
    """Desenha uma mensagem centralizada em um eixo vazio."""
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, message, ha="center", va="center",
            transform=ax.transAxes, fontsize=14, color="gray")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()


def _setup_xy_grid(
    ax: Axes,
    xlabel: str,
    xlim: int,
    major: list[int],
    minor: list[int],
    ylabel: str = "TAXA (%)",
) -> None:
    """Configura rótulos, limites e grades dos eixos do gráfico."""
    ax.set_xlabel(xlabel)
    ax.set_xlim(0, xlim)
    ax.set_xticks(major)
    ax.set_xticks(minor, minor=True)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.15, linestyle="--")


def _nearest_rate(
    day_rates: dict[int, float], pos: int, tolerance: int
) -> float | None:
    """Devolve a taxa mais próxima de ``pos`` dentro de ``tolerance``."""
    nearest = min(day_rates.keys(), key=lambda d: abs(d - pos))
    if abs(nearest - pos) <= tolerance:
        return day_rates[nearest]
    return None


def _draw_evolution_arrows(
    ax: Axes,
    dates_sorted: list[str],
    ticks: list[int],
    cmap: Colormap,
    sample: Callable[[str, int], float | None],
) -> None:
    """Desenha setas das transições ano a ano entre datas consecutivas."""
    import numpy as np
    for tick_idx, tick in enumerate(ticks):
        rates_seq = []
        for date_str in dates_sorted:
            rate = sample(date_str, tick)
            if rate is not None:
                rates_seq.append(rate)
        if len(rates_seq) < 2:
            continue
        trans_idx = (tick_idx - 1) % 5
        if trans_idx >= len(rates_seq) - 1:
            continue
        n_transitions = len(rates_seq) - 1
        ax.quiver(
            [tick + trans_idx * 0.06], [rates_seq[trans_idx]], [0.06],
            [rates_seq[trans_idx + 1] - rates_seq[trans_idx]],
            angles='xy', scale_units='xy', scale=1,
            color=cmap(np.linspace(0.3, 0.9, n_transitions))[trans_idx],
            width=0.004, zorder=5,
        )


def render_chart(fig: Figure, records: list[RateRecord], consolidated: bool = False) -> None:
    """Renderiza o gráfico principal de taxas, consolidado por ano ou por dia útil.

    No modo ``consolidated`` desenha as taxas mínima e máxima por ano em azul e
    vermelho, com marcas a cada 3 anos e menores a cada 1 ano. No modo padrão
    desenha a curva completa por dia útil, com marcas maiores a cada 66 dias
    úteis e menores a cada 22.
    """
    fig.clf()
    if not records:
        _render_empty(
            fig,
            "Nenhum dado carregado.\nInforme uma data e clique em Buscar.",
            "DC365",
            "TAXA",
        )
        return
    ax = fig.add_subplot(111)
    if consolidated:
        from b3_selic_pre.application.use_cases import consolidate_by_year
        grouped = consolidate_by_year(records)
        years = [g["year"] for g in grouped]
        min_rates = [g["min_rate"] for g in grouped]
        max_rates = [g["max_rate"] for g in grouped]
        ax.plot(years, min_rates, color="blue", marker="o",
                linestyle="-", linewidth=1.5, label="Menor taxa")
        ax.plot(years, max_rates, color="red", marker="o",
                linestyle="-", linewidth=1.5, label="Maior taxa")
        all_years = sorted({g["year"] for g in grouped})
        major_3yr = _nearest_ticks(all_years, range(0, 21, 3), 1)
        minor_1yr = _nearest_ticks(all_years, range(21), 1, set(major_3yr))
        _setup_xy_grid(ax, "Ano", 20, major_3yr, minor_1yr)
        ax.legend()
    else:
        days = [r.day252 for r in records]
        rates = [float(r.rate.replace(",", ".")) for r in records]
        ax.plot(days, rates, color="green", marker=".",
                linestyle="-", linewidth=1.5)
        all_days = sorted({r.day252 for r in records})
        major_66du = _nearest_ticks(all_days, range(66, 757, 66), 44)
        minor_22du = _nearest_ticks(all_days, range(1, 757, 22), 22, set(major_66du))
        _setup_xy_grid(ax, "Dias úteis", 756, major_66du, minor_22du)
    fig.tight_layout()


def render_curve_evolution(fig: Figure, date_rates: dict[str, list[RateRecord]]) -> None:
    """Renderiza a evolução das curvas de taxa ao longo das datas.

    Cada data é desenhada como uma linha em um tom de azul, com transparência
    e espessura crescentes para as datas mais recentes. Setas mostram a
    transição das taxas ano a ano entre as datas consecutivas.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    fig.clf()
    if not date_rates:
        _render_empty(fig, "Sem dados", "Ano", "TAXA")
        return
    ax = fig.add_subplot(111)
    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.6, 1.0, n)
    linewidths = np.linspace(1.5, 2.5, n)
    for i, date_str in enumerate(dates_sorted):
        rates = average_rate_by_year(date_rates[date_str])
        years = sorted(rates.keys())
        vals = [rates[y] for y in years]
        ax.plot(years, vals, color=colors[i], alpha=alphas[i],
                linewidth=linewidths[i], label=date_str)
    all_years = sorted(average_rate_by_year(date_rates[dates_sorted[-1]]).keys())
    major_3yr = _nearest_ticks(all_years, range(0, 21, 3), 1)
    minor_1yr = _nearest_ticks(all_years, range(21), 1, set(major_3yr))
    sample = lambda date_str, tick: average_rate_by_year(date_rates[date_str]).get(tick)
    _draw_evolution_arrows(ax, dates_sorted, all_years, plt.cm.Blues, sample)
    _setup_xy_grid(ax, "Ano", 20, major_3yr, minor_1yr)
    ax.legend(fontsize=8)
    fig.tight_layout()


def render_detailed_evolution(fig: Figure, date_rates: dict[str, list[RateRecord]]) -> None:
    """Renderiza a evolução detalhada das curvas por dia útil.

    Cada data é desenhada como uma linha em um tom de verde. Setas indicam a
    transição das taxas para cada vencimento entre datas consecutivas, com
    marcações no eixo a cada 66 e 22 dias úteis.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    fig.clf()
    if not date_rates:
        _render_empty(fig, "Sem dados", "Dias úteis", "TAXA")
        return
    ax = fig.add_subplot(111)
    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Greens(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.6, 1.0, n)
    linewidths = np.linspace(1.5, 2.5, n)
    for i, date_str in enumerate(dates_sorted):
        records = date_rates[date_str]
        days = [r.day252 for r in records]
        rates = [float(r.rate.replace(",", ".")) for r in records]
        ax.plot(days, rates, color=colors[i], alpha=alphas[i],
                linewidth=linewidths[i], label=date_str)
    date_rate_map = {
        date_str: {r.day252: float(r.rate.replace(",", ".")) for r in date_rates[date_str]}
        for date_str in dates_sorted
    }
    all_day_values = sorted({r.day252 for r in date_rates[dates_sorted[-1]]})
    major_66du = _nearest_ticks(all_day_values, range(66, 757, 66), 44)
    minor_22du = _nearest_ticks(all_day_values, range(1, 757, 22), 22, set(major_66du))
    sample = lambda date_str, pos: _nearest_rate(date_rate_map[date_str], pos, 22)
    _draw_evolution_arrows(ax, dates_sorted, minor_22du, plt.cm.Greens, sample)
    _setup_xy_grid(ax, "Dias úteis", 756, major_66du, minor_22du)
    ax.legend(fontsize=8)
    fig.tight_layout()


def _consolidated_3d_data(
    date_rates: dict[str, list[RateRecord]], dates_sorted: list[str]
) -> tuple[list[dict[int, float]], np.ndarray, np.ndarray]:
    """Constrói as grades X/Z consolidadas por ano para a superfície 3D."""
    import numpy as np
    per_date_rates = [average_rate_by_year(date_rates[d]) for d in dates_sorted]
    all_years = set()
    for rates in per_date_rates:
        all_years.update(rates.keys())
    years = sorted(y for y in all_years if 0 <= y <= 20)
    X = np.tile(np.array(years), (len(dates_sorted), 1))
    Z = np.array([
        [rates.get(y, np.nan) for y in years]
        for rates in per_date_rates
    ])
    return per_date_rates, X, Z


def _daily_3d_data(
    date_rates: dict[str, list[RateRecord]], dates_sorted: list[str]
) -> tuple[list[tuple[list[int], list[float]]], np.ndarray, np.ndarray]:
    """Constrói as grades X/Z por dia útil para a superfície 3D."""
    import numpy as np
    per_date_data = []
    all_days = set()
    for date_str in dates_sorted:
        records = date_rates[date_str]
        days = [r.day252 for r in records if r.day252 <= 756]
        rates = [float(r.rate.replace(",", ".")) for r in records if r.day252 <= 756]
        per_date_data.append((days, rates))
        all_days.update(days)
    max_day = max(all_days) if all_days else 0
    common_x = np.linspace(0, max_day, num=200)
    X = np.tile(common_x, (len(dates_sorted), 1))
    Z = np.array([
        np.interp(common_x, days, rates, left=np.nan, right=np.nan)
        for days, rates in per_date_data
    ])
    return per_date_data, X, Z


def _plot_3d_consolidated_lines(
    ax: Axes, per_date_rates: list[dict[int, float]], z_indices: list[int]
) -> None:
    """Traça a curva consolidada de cada data sobre a superfície 3D."""
    n = len(z_indices)
    for i in range(n - 1, -1, -1):
        rates = per_date_rates[i]
        x_vals = sorted(y for y in rates if 0 <= y <= 20)
        y_vals = [rates[y] for y in x_vals]
        ax.plot(x_vals, [z_indices[i]] * len(x_vals), y_vals,
                color="black", linewidth=(n - 1 - i) * 0.425 + 0.8, alpha=0.7)


def _plot_3d_daily_lines(
    ax: Axes, per_date_data: list[tuple[list[int], list[float]]], z_indices: list[int]
) -> None:
    """Traça a curva por dia útil de cada data sobre a superfície 3D."""
    n = len(z_indices)
    for i in range(n - 1, -1, -1):
        days, rates = per_date_data[i]
        if not days:
            continue
        ax.plot(days, [z_indices[i]] * len(days), rates,
                color="black", linewidth=(n - 1 - i) * 0.425 + 0.8, alpha=0.7)


def _interpolate_3d_surface(
    X: np.ndarray, Z: np.ndarray, z_indices: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Interpola a superfície 3D em uma grade fina entre as datas."""
    import numpy as np
    z_arr = np.array(z_indices)
    y_fine = np.linspace(z_arr.min(), z_arr.max(), len(z_indices) * 20)
    X_fine = np.full((len(y_fine), X.shape[1]), np.nan)
    Y_fine = np.tile(y_fine, (X.shape[1], 1)).T
    Z_fine = np.full((len(y_fine), Z.shape[1]), np.nan)
    for j in range(Z.shape[1]):
        col = Z[:, j]
        good = ~np.isnan(col)
        if good.sum() >= 2:
            Z_fine[:, j] = np.interp(y_fine, z_arr[good], col[good])
            X_fine[:, j] = np.interp(y_fine, z_arr[good], X[good, j])
        elif good.sum() == 1:
            Z_fine[:, j] = col[good][0]
            X_fine[:, j] = X[good, j].mean()
        else:
            Z_fine[:, j] = np.nan
            X_fine[:, j] = np.nan
    return X_fine, Y_fine, Z_fine


def render_3d_evolution(
    fig: Figure, date_rates: dict[str, list[RateRecord]], consolidated: bool = False
) -> None:
    """Renderiza a evolução 3D das taxas, consolidada por ano ou por dia útil.

    Cada data ocupa uma fatia do eixo de períodos. A superfície é interpolada
    para suavizar a transição entre as fatias, e a cor (verde a vermelho)
    reflete o nível da taxa. Linhas pretas traçam a curva de cada data.
    """
    fig.clf()
    if not date_rates:
        _render_empty(
            fig, "Sem dados", "Ano" if consolidated else "Dias úteis", "Taxa"
        )
        return
    ax = fig.add_subplot(111, projection='3d')
    dates_sorted = sorted(date_rates.keys(), reverse=True)
    z_indices = list(range(len(dates_sorted)))
    if consolidated:
        data, X, Z = _consolidated_3d_data(date_rates, dates_sorted)
        _plot_3d_consolidated_lines(ax, data, z_indices)
        ax.set_xlabel("Ano")
        ax.set_xlim(0, 20)
    else:
        data, X, Z = _daily_3d_data(date_rates, dates_sorted)
        _plot_3d_daily_lines(ax, data, z_indices)
        ax.set_xlabel("Dias úteis")
        ax.set_xlim(0, 756)
    X_fine, Y_fine, Z_fine = _interpolate_3d_surface(X, Z, z_indices)
    surf = ax.plot_surface(X_fine, Y_fine, Z_fine, cmap="RdYlGn_r", alpha=0.85,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, label="Taxa %", shrink=0.6)
    ax.set_ylabel("Período")
    ax.set_zlabel("Taxa %")
    ax.view_init(elev=25, azim=-60)
    ax.set_yticks(z_indices)
    ax.set_yticklabels(dates_sorted, fontsize=8)
    fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
