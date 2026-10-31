"""Controle compartilhado de cursor de espera e overlays de processamento."""

from __future__ import annotations

import weakref
from collections.abc import Iterator
from typing import Any

Widget = Any
BUSY_TEXT = "Processando as informações. Aguarde…"


class _CursorState:
    """Contagem de referências do cursor para uma janela raiz."""

    def __init__(self: _CursorState) -> None:
        """Start with no references and no saved cursors."""
        self.depth = 0
        self.originals: dict[object, str] = {}


_states: weakref.WeakKeyDictionary[object, _CursorState] = (
    weakref.WeakKeyDictionary()
)


def _state_for(root: object) -> _CursorState:
    """Return the cursor state for ``root``, creating it when necessary."""
    state = _states.get(root)
    if state is None:
        state = _CursorState()
        try:
            _states[root] = state
        except TypeError:
            return _CursorState()
    return state


def _walk(widget: object) -> Iterator[object]:
    """Yield ``widget`` and all descendants that expose ``winfo_children``."""
    yield widget
    try:
        children = widget.winfo_children()  # type: ignore[attr-defined]
    except Exception:
        return
    for child in children:
        yield from _walk(child)


def _apply_tree(root: object, originals: dict[object, str]) -> None:
    """Set the wait cursor on the tree, preserving each widget's original."""
    for widget in _walk(root):
        try:
            if widget in originals:
                widget.config(cursor="watch")  # type: ignore[attr-defined]
                continue
            original = widget.cget("cursor")  # type: ignore[attr-defined]
            widget.config(cursor="watch")  # type: ignore[attr-defined]
            originals[widget] = original
        except Exception:
            pass


def _restore_tree(originals: dict[object, str]) -> None:
    """Restore every widget cursor saved by :func:`_apply_tree`."""
    for widget, cursor in list(originals.items()):
        try:
            widget.config(cursor=cursor)  # type: ignore[attr-defined]
        except Exception:
            pass
    originals.clear()


class WaitCursor:
    """Aplica o cursor ``watch`` com contagem por janela raiz."""

    def __init__(
        self: WaitCursor, root: Widget
    ) -> None:
        """Store the root window whose cursor will be changed."""
        self.root = root
        self._entered = False

    @property
    def active(self: WaitCursor) -> bool:
        """Return whether this instance currently holds a reference."""
        return self._entered

    def enter(self: WaitCursor) -> None:
        """Take a reference and show the wait cursor on the first one."""
        if self._entered:
            return
        self._entered = True
        state = _state_for(self.root)
        state.depth += 1
        if state.depth == 1:
            _apply_tree(self.root, state.originals)

    def refresh(self: WaitCursor) -> None:
        """Apply the wait cursor to widgets created during the busy state."""
        if not self._entered:
            return
        state = _states.get(self.root)
        if state is not None and state.depth:
            _apply_tree(self.root, state.originals)

    def leave(self: WaitCursor) -> None:
        """Release a reference and restore the cursor on the last one."""
        if not self._entered:
            return
        self._entered = False
        state = _states.get(self.root)
        if state is None:
            return
        state.depth = max(0, state.depth - 1)
        if state.depth:
            return
        _restore_tree(state.originals)
        _states.pop(self.root, None)


class BusyIndicator:
    """Combina o cursor de espera com um overlay opcional."""

    def __init__(
        self: BusyIndicator,
        root: Widget,
        overlay: Widget | None = None,
        *,
        label: Widget | None = None,
    ) -> None:
        """Store the root, the optional overlay and its wait cursor."""
        self.root = root
        self.overlay = overlay if overlay is not None else label
        self._cursor = WaitCursor(root)
        self._depth = 0
        self._overlay_shown = False

    @property
    def active(self: BusyIndicator) -> bool:
        """Return whether the indicator currently holds a reference."""
        return self._depth > 0

    def enter(self: BusyIndicator, *, show_overlay: bool = True) -> None:
        """Take a cursor reference and optionally show the overlay."""
        if self._depth == 0:
            self._cursor.enter()
        if show_overlay and not self._overlay_shown:
            self._show_overlay()
            self._overlay_shown = True
        self._depth += 1

    def leave(self: BusyIndicator) -> None:
        """Hide the overlay and release the cursor on the last exit."""
        if self._depth == 0:
            return
        self._depth -= 1
        if self._depth:
            return
        if self._overlay_shown:
            self._hide_overlay()
            self._overlay_shown = False
        self._cursor.leave()

    def reset(self: BusyIndicator) -> None:
        """Release every reference held by this indicator."""
        if self._depth == 0:
            return
        self._depth = 0
        if self._overlay_shown:
            self._hide_overlay()
            self._overlay_shown = False
        self._cursor.leave()

    def raise_overlay(self: BusyIndicator) -> None:
        """Refresh the cursor and keep the overlay above new widgets."""
        if self._depth == 0:
            return
        self._cursor.refresh()
        if self._overlay_shown and self.overlay is not None:
            self._show_overlay()

    def _show_overlay(self: BusyIndicator) -> None:
        if self.overlay is None:
            return
        try:
            self.overlay.place(relx=0.5, rely=0.5, anchor="center")
            self.overlay.lift()
        except Exception:
            return

    def _hide_overlay(self: BusyIndicator) -> None:
        if self.overlay is None:
            return
        try:
            self.overlay.place_forget()
        except Exception:
            return


__all__ = ["BUSY_TEXT", "BusyIndicator", "WaitCursor"]
