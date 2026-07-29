from datetime import datetime, timezone


def default_reference_date():
    return datetime.now(timezone.utc).date().isoformat()


def validate_reference_date(reference_date):
    try:
        parsed = datetime.strptime(reference_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
    except ValueError as exc:
        raise ValueError("Use uma data no formato YYYY-MM-DD.") from exc
    return parsed.isoformat()


def _days_ago(base_date, days):
    from datetime import timedelta
    d = datetime.strptime(base_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
    return (d - timedelta(days=days)).isoformat()


def consolidate_by_year(records):
    groups = {}
    for r in records:
        year = r.day360 // 365
        rate = float(r.rate.replace(",", "."))
        if year in groups:
            g = groups[year]
            g["min_rate"] = min(g["min_rate"], rate)
            g["max_rate"] = max(g["max_rate"], rate)
        else:
            groups[year] = {"year": year, "min_rate": rate, "max_rate": rate}
    return [groups[y] for y in sorted(groups)]


def average_rate_by_year(records):
    consolidated = consolidate_by_year(records)
    return {g["year"]: (g["min_rate"] + g["max_rate"]) / 2 for g in consolidated}
