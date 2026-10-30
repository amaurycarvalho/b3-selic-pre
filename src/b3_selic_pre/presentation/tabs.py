"""Registro headless de abas com construção lazy por visibilidade."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

TabFactory = Callable[[], Any]


@dataclass(frozen=True)
class TabSpec:
    """Definição imutável de uma aba registrada no shell."""

    tab_id: str
    label: str
    factory: TabFactory


class LazyTabRegistry:
    """Mantém a ordem das abas e constrói cada uma só na primeira exibição."""

    def __init__(self: LazyTabRegistry, specs: Iterable[TabSpec] = ()) -> None:
        """Register the initial specs in deterministic order."""
        self._specs: list[TabSpec] = []
        self._by_id: dict[str, TabSpec] = {}
        self._built: dict[str, object] = {}
        self._visible: str | None = None
        for spec in specs:
            self.register(spec)

    def register(self: LazyTabRegistry, spec: TabSpec) -> None:
        """Append a tab, rejecting duplicate identifiers."""
        if spec.tab_id in self._by_id:
            raise ValueError(f"Aba duplicada: {spec.tab_id}.")
        self._specs.append(spec)
        self._by_id[spec.tab_id] = spec

    def spec(self: LazyTabRegistry, tab_id: str) -> TabSpec:
        """Return the spec for ``tab_id``."""
        try:
            return self._by_id[tab_id]
        except KeyError as exc:
            raise KeyError(f"Aba desconhecida: {tab_id}.") from exc

    def ordered_specs(self: LazyTabRegistry) -> tuple[TabSpec, ...]:
        """Return specs in registration order."""
        return tuple(self._specs)

    def is_built(self: LazyTabRegistry, tab_id: str) -> bool:
        """Return whether the tab content already exists."""
        return tab_id in self._built

    def ensure_built(self: LazyTabRegistry, tab_id: str) -> object:
        """Build the tab once and return its controller on later calls."""
        spec = self.spec(tab_id)
        if tab_id not in self._built:
            self._built[tab_id] = spec.factory()
        return self._built[tab_id]

    def mark_visible(self: LazyTabRegistry, tab_id: str) -> object:
        """Record the visible tab and ensure its content is built."""
        built = self.ensure_built(tab_id)
        self._visible = tab_id
        return built

    @property
    def visible_id(self: LazyTabRegistry) -> str | None:
        """Return the last tab marked visible."""
        return self._visible

    def built_ids(self: LazyTabRegistry) -> tuple[str, ...]:
        """Return the identifiers already built, in registration order."""
        return tuple(
            spec.tab_id for spec in self._specs if spec.tab_id in self._built
        )
