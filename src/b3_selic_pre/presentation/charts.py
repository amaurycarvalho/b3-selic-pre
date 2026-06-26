from b3_selic_pre.application.use_cases import average_rate_by_year


def _nearest_ticks(all_values, targets, tolerance, exclude_set=None):
    result = []
    seen = set(exclude_set) if exclude_set else set()
    for target in targets:
        nearest = min(all_values, key=lambda d: abs(d - target))
        if abs(nearest - target) <= tolerance and nearest not in seen:
            result.append(nearest)
            seen.add(nearest)
    return result


def _interpolate_rates(records, common_x):
    import numpy as np
    days = [r.day252 for r in records]
    rates = [float(r.rate.replace(",", ".")) for r in records]
    return np.interp(common_x, days, rates, left=np.nan, right=np.nan)


def render_chart(fig, records, consolidated=False):
    fig.clf()
    ax = fig.add_subplot(111)
    if not records:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("DC365")
        ax.set_ylabel("TAXA")
        fig.tight_layout()
        return
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
        ax.set_xlabel("Ano")
        ax.set_xlim(0, 20)
        all_years = sorted(set(g["year"] for g in grouped))
        major_3yr = _nearest_ticks(all_years, range(0, 21, 3), 1)
        minor_1yr = _nearest_ticks(all_years, range(0, 21), 1, set(major_3yr))
        ax.set_xticks(major_3yr)
        ax.set_xticks(minor_1yr, minor=True)
        ax.legend()
    else:
        days = [r.day252 for r in records]
        rates = [float(r.rate.replace(",", ".")) for r in records]
        ax.plot(days, rates, color="green", marker=".",
                linestyle="-", linewidth=1.5)
        ax.set_xlabel("Dias úteis")
        ax.set_xlim(0, 756)
        all_days = sorted(set(r.day252 for r in records))
        major_66du = _nearest_ticks(all_days, range(66, 757, 66), 44)
        minor_22du = _nearest_ticks(all_days, range(1, 757, 22), 22, set(major_66du))
        ax.set_xticks(major_66du)
        ax.set_xticks(minor_22du, minor=True)
    ax.set_ylabel("TAXA (%)")
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.15, linestyle="--")
    fig.tight_layout()


def render_curve_evolution(fig, date_rates):
    import numpy as np
    import matplotlib.pyplot as plt
    fig.clf()
    ax = fig.add_subplot(111)
    if not date_rates:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("Ano")
        ax.set_ylabel("TAXA")
        fig.tight_layout()
        return
    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.3, 1.0, n)
    linewidths = np.linspace(0.8, 2.5, n)
    all_rates = []
    for i, date_str in enumerate(dates_sorted):
        rates = average_rate_by_year(date_rates[date_str])
        years = sorted(rates.keys())
        vals = [rates[y] for y in years]
        all_rates.append((years, vals))
        ax.plot(years, vals, color=colors[i], alpha=alphas[i],
                linewidth=linewidths[i], label=date_str)
    all_years = sorted(average_rate_by_year(date_rates[dates_sorted[-1]]).keys())
    major_3yr = _nearest_ticks(all_years, range(0, 21, 3), 1)
    minor_1yr = _nearest_ticks(all_years, range(0, 21), 1, set(major_3yr))
    for tick_idx, year in enumerate(all_years):
        rates_seq = []
        for date_str in dates_sorted:
            yearly_rates = average_rate_by_year(date_rates[date_str])
            if year in yearly_rates:
                rates_seq.append(yearly_rates[year])
        if len(rates_seq) < 2:
            continue
        trans_idx = (tick_idx - 1) % 5
        if trans_idx >= len(rates_seq) - 1:
            continue
        n_transitions = len(rates_seq) - 1
        X = [year + trans_idx * 0.06]
        Y = [rates_seq[trans_idx]]
        U = [0.06]
        V = [rates_seq[trans_idx + 1] - rates_seq[trans_idx]]
        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=1,
                  color=plt.cm.Blues(np.linspace(0.3, 0.9, n_transitions))[trans_idx],
                  width=0.004, zorder=5)
    ax.set_xlabel("Ano")
    ax.set_xlim(0, 20)
    ax.set_xticks(major_3yr)
    ax.set_xticks(minor_1yr, minor=True)
    ax.set_ylabel("TAXA (%)")
    ax.legend(fontsize=8)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.15, linestyle="--")
    fig.tight_layout()


def render_detailed_evolution(fig, date_rates):
    import numpy as np
    import matplotlib.pyplot as plt
    fig.clf()
    ax = fig.add_subplot(111)
    if not date_rates:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("Dias úteis")
        ax.set_ylabel("TAXA")
        fig.tight_layout()
        return
    dates_sorted = sorted(date_rates.keys())
    n = len(dates_sorted)
    colors = plt.cm.Greens(np.linspace(0.3, 0.9, n))
    alphas = np.linspace(0.3, 1.0, n)
    linewidths = np.linspace(0.8, 2.5, n)
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
    all_day_values = sorted(set(r.day252 for r in date_rates[dates_sorted[-1]]))
    major_66du = _nearest_ticks(all_day_values, range(66, 757, 66), 44)
    minor_22du = _nearest_ticks(all_day_values, range(1, 757, 22), 22, set(major_66du))
    for tick_idx, pos in enumerate(minor_22du):
        rates_seq = []
        for date_str in dates_sorted:
            day_rates = date_rate_map[date_str]
            nearest = min(day_rates.keys(), key=lambda d: abs(d - pos))
            if abs(nearest - pos) <= 22:
                rates_seq.append(day_rates[nearest])
        if len(rates_seq) < 2:
            continue
        trans_idx = (tick_idx - 1) % 5
        if trans_idx >= len(rates_seq) - 1:
            continue
        n_transitions = len(rates_seq) - 1
        X = [pos + trans_idx * 0.06]
        Y = [rates_seq[trans_idx]]
        U = [0.06]
        V = [rates_seq[trans_idx + 1] - rates_seq[trans_idx]]
        ax.quiver(X, Y, U, V, angles="xy", scale_units="xy", scale=1,
                  color=plt.cm.Greens(np.linspace(0.3, 0.9, n_transitions))[trans_idx],
                  width=0.004, zorder=5)
    ax.set_xlabel("Dias úteis")
    ax.set_xlim(0, 756)
    ax.set_xticks(major_66du)
    ax.set_xticks(minor_22du, minor=True)
    ax.set_ylabel("TAXA (%)")
    ax.legend(fontsize=8)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.15, linestyle="--")
    fig.tight_layout()


def render_3d_evolution(fig, date_rates, consolidated=False):
    import numpy as np
    import matplotlib.pyplot as plt
    fig.clf()
    if not date_rates:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                transform=ax.transAxes, fontsize=14, color="gray")
        ax.set_xlabel("Ano" if consolidated else "Dias úteis")
        ax.set_ylabel("Taxa")
        fig.tight_layout()
        return
    ax = fig.add_subplot(111, projection='3d')
    dates_sorted = sorted(date_rates.keys(), reverse=True)
    n = len(dates_sorted)
    z_indices = list(range(n))
    if consolidated:
        all_years = set()
        per_date_rates = []
        for date_str in dates_sorted:
            rates = average_rate_by_year(date_rates[date_str])
            per_date_rates.append(rates)
            all_years.update(rates.keys())
        years = sorted(y for y in all_years if 0 <= y <= 20)
        X, Y = np.meshgrid(years, z_indices)
        Z = np.array([
            [per_date_rates[i].get(y, np.nan) for y in years]
            for i in range(n)
        ])
        ax.set_xlabel("Ano")
        for i in range(n - 1, -1, -1):
            rates = per_date_rates[i]
            x_vals = sorted(y for y in rates if 0 <= y <= 20)
            y_vals = [rates[y] for y in x_vals]
            ax.plot(x_vals, [z_indices[i]] * len(x_vals), y_vals,
                    color="black", linewidth=(n - 1 - i) * 0.425 + 0.8, alpha=0.7)
    else:
        all_days = set()
        per_date_data = []
        for date_str in dates_sorted:
            records = date_rates[date_str]
            days = [r.day252 for r in records if r.day252 <= 756]
            rates = [float(r.rate.replace(",", ".")) for r in records if r.day252 <= 756]
            per_date_data.append((days, rates))
            all_days.update(days)
        max_day = max(all_days) if all_days else 0
        common_x = np.linspace(0, max_day, num=200)
        X, Y = np.meshgrid(common_x, z_indices)
        Z = np.array([
            np.interp(common_x, days, rates, left=np.nan, right=np.nan)
            for days, rates in per_date_data
        ])
        ax.set_xlabel("Dias úteis")
        for i in range(n - 1, -1, -1):
            days, rates = per_date_data[i]
            if not days:
                continue
            ax.plot(days, [z_indices[i]] * len(days), rates,
                    color="black", linewidth=(n - 1 - i) * 0.425 + 0.8, alpha=0.7)
    if consolidated:
        ax.set_xlim(0, 20)
    else:
        ax.set_xlim(0, 756)
    z_arr = np.array(z_indices)
    y_fine = np.linspace(z_arr.min(), z_arr.max(), n * 20)
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
    surf = ax.plot_surface(X_fine, Y_fine, Z_fine, cmap="RdYlGn_r", alpha=0.85,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, label="Taxa %", shrink=0.6)
    ax.set_ylabel("Período")
    ax.set_zlabel("Taxa %")
    ax.view_init(elev=25, azim=-60)
    ax.set_yticks(z_indices)
    ax.set_yticklabels(dates_sorted, fontsize=8)
    fig.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
