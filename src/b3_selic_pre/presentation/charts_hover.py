"""Rótulos interativos (hover) para os gráficos analíticos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.axes import Axes

HoverPoint = tuple[float, float, str]
Canvas = Any
Event = Any
Transform = Any
_THRESHOLD_PX = 20


def register_hover(ax: Axes, points: list[HoverPoint]) -> None:
    """Attach hover points to an axes for later cursor lookup."""
    ax._hover_points = points  # type: ignore[attr-defined]


class HoverTooltip:
    """Mostra o conteúdo do ponto de dados mais próximo do cursor."""

    def __init__(self: HoverTooltip, canvas: Canvas) -> None:
        """Connect the hover handler to the matplotlib canvas."""
        self.canvas = canvas
        self._annotation = None
        self._last_key: tuple[float, float, str] | None = None
        self._cid = canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _on_motion(self: HoverTooltip, event: Event) -> None:
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            self._hide()
            return
        points = getattr(event.inaxes, "_hover_points", None)
        if not points:
            self._hide()
            return
        transform = event.inaxes.transData
        nearest = min(
            points,
            key=lambda point: _distance_px(transform, point, event),
        )
        if _distance_px(transform, nearest, event) > _THRESHOLD_PX:
            self._hide()
            return
        if nearest != self._last_key:
            self._last_key = nearest
            self._show(event.inaxes, nearest)

    def _show(self: HoverTooltip, ax: Axes, point: HoverPoint) -> None:
        if self._annotation is None or self._annotation.axes is not ax:
            self._annotation = ax.annotate(
                point[2],
                xy=(point[0], point[1]),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=8,
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "fc": "#ffffe0",
                    "ec": "#888888",
                    "alpha": 0.95,
                },
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#888888",
                    "shrinkA": 0,
                    "shrinkB": 0,
                },
                zorder=10,
            )
        else:
            self._annotation.xy = (point[0], point[1])
            self._annotation.set_text(point[2])
            self._annotation.set_visible(True)
        self.canvas.draw_idle()

    def _hide(self: HoverTooltip) -> None:
        if self._annotation is None or not self._annotation.get_visible():
            return
        self._annotation.set_visible(False)
        self._last_key = None
        self.canvas.draw_idle()


def _distance_px(
    transform: Transform, point: HoverPoint, event: Event
) -> float:
    x_px, y_px = transform.transform((point[0], point[1]))
    return ((x_px - event.x) ** 2 + (y_px - event.y) ** 2) ** 0.5
