"""View-model headless da aba ``Feriados``."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from b3_selic_pre.application.calendar.ports import YearHolidays
from b3_selic_pre.presentation.calendar_text import weekday_abbreviation

MONTH_NAMES = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)
EMPTY_TEXT = (
    "Sem feriados em cache. Use o botão de atualização para consultar a ANBIMA."
)


@dataclass(frozen=True)
class HolidayItem:
    """Um feriado já formatado para a árvore e o texto."""

    data: date
    nome: str
    origem: str

    @property
    def label(self: HolidayItem) -> str:
        """Return the ``DD (abrev)`` tree label."""
        return f"{self.data.day:02d} ({weekday_abbreviation(self.data)})"

    @property
    def line(self: HolidayItem) -> str:
        """Return the full line with the weekday and name."""
        return f"{self.label} - {self.nome}"


@dataclass(frozen=True)
class MonthNode:
    """Ramo de mês com os feriados do mês."""

    year: int
    month: int
    holidays: tuple[HolidayItem, ...]

    @property
    def iid(self: MonthNode) -> str:
        """Return the stable tree identifier."""
        return f"y{self.year}m{self.month:02d}"

    @property
    def label(self: MonthNode) -> str:
        """Return the ``MM - Nome`` tree label."""
        return f"{self.month:02d} - {MONTH_NAMES[self.month - 1]}"


@dataclass(frozen=True)
class YearNode:
    """Ramo de ano com os meses que possuem feriados."""

    year: int
    months: tuple[MonthNode, ...]

    @property
    def iid(self: YearNode) -> str:
        """Return the stable tree identifier."""
        return f"y{self.year}"

    @property
    def label(self: YearNode) -> str:
        """Return the year tree label."""
        return str(self.year)


@dataclass(frozen=True)
class TreeRow:
    """Uma linha a inserir no ``ttk.Treeview``."""

    iid: str
    parent: str
    text: str
    kind: str


class FeriadosViewModel:
    """Árvore e textos derivados dos anos em cache."""

    def __init__(
        self: FeriadosViewModel, years: Sequence[YearHolidays]
    ) -> None:
        """Build the deterministic year/month/day tree."""
        self.years = tuple(self._build_years(years))
        self._texts = self._build_texts()

    @staticmethod
    def _build_years(years: Sequence[YearHolidays]) -> list[YearNode]:
        nodes: list[YearNode] = []
        for data in sorted(years, key=lambda item: item.year, reverse=True):
            if not data.published:
                continue
            items = [
                HolidayItem(holiday.date, holiday.name, data.source)
                for holiday in data.holidays
            ]
            grouped: dict[int, list[HolidayItem]] = {}
            for item in sorted(items, key=lambda value: value.data):
                grouped.setdefault(item.data.month, []).append(item)
            months = tuple(
                MonthNode(data.year, month, tuple(grouped[month]))
                for month in sorted(grouped)
            )
            if months:
                nodes.append(YearNode(data.year, months))
        return nodes

    def _build_texts(self: FeriadosViewModel) -> dict[str, str]:
        texts: dict[str, str] = {}
        for year_node in self.years:
            texts[year_node.iid] = self._year_text(year_node)
            for month_node in year_node.months:
                texts[month_node.iid] = self._month_text(month_node)
                for item in month_node.holidays:
                    texts[self._day_iid(item)] = self._day_text(item)
        return texts

    @staticmethod
    def _day_iid(item: HolidayItem) -> str:
        return (
            f"y{item.data.year}m{item.data.month:02d}"
            f"d{item.data.day:02d}"
        )

    @staticmethod
    def _year_text(node: YearNode) -> str:
        lines = [node.label]
        for month in node.months:
            lines.append(f"  {month.label}")
            lines.extend(f"    {item.line}" for item in month.holidays)
        return "\n".join(lines)

    @staticmethod
    def _month_text(node: MonthNode) -> str:
        lines = [f"{node.label} de {node.year}"]
        lines.extend(f"  {item.line}" for item in node.holidays)
        return "\n".join(lines)

    @staticmethod
    def _day_text(item: HolidayItem) -> str:
        return (
            f"{item.data.isoformat()} "
            f"({weekday_abbreviation(item.data)}) - {item.nome}"
        )

    @property
    def rows(self: FeriadosViewModel) -> tuple[TreeRow, ...]:
        """Return every tree row in display order."""
        rows: list[TreeRow] = []
        for year_node in self.years:
            rows.append(
                TreeRow(year_node.iid, "", year_node.label, "year")
            )
            for month_node in year_node.months:
                rows.append(
                    TreeRow(
                        month_node.iid,
                        year_node.iid,
                        month_node.label,
                        "month",
                    )
                )
                for item in month_node.holidays:
                    rows.append(
                        TreeRow(
                            self._day_iid(item),
                            month_node.iid,
                            item.label,
                            "day",
                        )
                    )
        return tuple(rows)

    def text_for(self: FeriadosViewModel, iid: str) -> str:
        """Return the textbox content for a tree identifier."""
        return self._texts.get(iid, EMPTY_TEXT)

    @property
    def is_empty(self: FeriadosViewModel) -> bool:
        """Return whether the tree has no years."""
        return not self.years

    def contains(self: FeriadosViewModel, iid: str | None) -> bool:
        """Return whether ``iid`` still exists in the tree."""
        return iid is not None and iid in self._texts


__all__ = [
    "EMPTY_TEXT",
    "MONTH_NAMES",
    "FeriadosViewModel",
    "HolidayItem",
    "MonthNode",
    "TreeRow",
    "YearNode",
]
