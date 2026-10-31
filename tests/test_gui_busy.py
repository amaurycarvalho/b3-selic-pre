"""Testes headless do indicador de ocupação compartilhado."""

from b3_selic_pre.presentation.busy import BusyIndicator, WaitCursor


class FakeWidget:
    def __init__(self, cursor="", children=()):
        self._cursor = cursor
        self.cursors = []
        self.children = list(children)
        self.fail = False

    def config(self, cursor):
        if self.fail:
            raise RuntimeError("janela destruída")
        self._cursor = cursor
        self.cursors.append(cursor)

    def cget(self, option):
        if option != "cursor":
            raise KeyError(option)
        return self._cursor

    def winfo_children(self):
        return self.children


FakeRoot = FakeWidget


class FakeOverlay:
    def __init__(self):
        self.places = []
        self.lifts = 0
        self.hidden = 0

    def place(self, **kwargs):
        self.places.append(kwargs)

    def lift(self):
        self.lifts += 1

    def place_forget(self):
        self.hidden += 1


def test_wait_cursor_uses_reference_count_per_root():
    root = FakeRoot()
    first = WaitCursor(root)
    second = WaitCursor(root)

    first.enter()
    second.enter()
    assert root.cursors == ["watch"]

    first.leave()
    assert root.cursors == ["watch"]

    second.leave()
    assert root.cursors == ["watch", ""]


def test_wait_cursor_ignores_double_enter_and_double_leave():
    root = FakeRoot()
    cursor = WaitCursor(root)

    cursor.enter()
    cursor.enter()
    cursor.leave()
    cursor.leave()

    assert root.cursors == ["watch", ""]


def test_wait_cursor_tolerates_destroyed_root():
    root = FakeRoot()
    root.fail = True
    cursor = WaitCursor(root)

    cursor.enter()
    cursor.leave()

    assert cursor.active is False


def test_wait_cursor_applies_and_restores_descendant_cursors():
    text = FakeWidget(cursor="xterm")
    canvas = FakeWidget(cursor="")
    root = FakeRoot(children=[text, canvas])
    cursor = WaitCursor(root)

    cursor.enter()
    assert root.cget("cursor") == "watch"
    assert text.cget("cursor") == "watch"
    assert canvas.cget("cursor") == "watch"

    cursor.leave()
    assert root.cget("cursor") == ""
    assert text.cget("cursor") == "xterm"
    assert canvas.cget("cursor") == ""


def test_wait_cursor_refresh_reaches_widgets_created_later():
    root = FakeRoot()
    cursor = WaitCursor(root)
    cursor.enter()

    text = FakeWidget(cursor="xterm")
    root.children.append(text)
    cursor.refresh()

    assert text.cget("cursor") == "watch"
    cursor.leave()
    assert text.cget("cursor") == "xterm"


def test_busy_indicator_shows_and_hides_overlay():
    root = FakeRoot()
    overlay = FakeOverlay()
    busy = BusyIndicator(root, overlay)

    busy.enter()
    assert busy.active
    assert root.cursors == ["watch"]
    assert overlay.places == [{"relx": 0.5, "rely": 0.5, "anchor": "center"}]
    assert overlay.lifts == 1

    busy.leave()
    assert busy.active is False
    assert root.cursors == ["watch", ""]
    assert overlay.hidden == 1


def test_busy_indicator_keeps_overlay_until_last_leave():
    root = FakeRoot()
    overlay = FakeOverlay()
    busy = BusyIndicator(root, overlay)

    busy.enter()
    busy.enter()
    busy.leave()
    assert busy.active
    assert overlay.hidden == 0
    assert root.cursors == ["watch"]

    busy.leave()
    assert overlay.hidden == 1
    assert root.cursors == ["watch", ""]


def test_busy_indicator_reset_releases_every_reference():
    root = FakeRoot()
    overlay = FakeOverlay()
    busy = BusyIndicator(root, overlay)

    busy.enter()
    busy.enter()
    busy.reset()
    busy.reset()

    assert busy.active is False
    assert overlay.hidden == 1
    assert root.cursors == ["watch", ""]


def test_busy_indicator_can_raise_overlay_above_new_widgets():
    root = FakeRoot()
    overlay = FakeOverlay()
    busy = BusyIndicator(root, overlay)
    busy.enter()

    text = FakeWidget(cursor="xterm")
    root.children.append(text)
    busy.raise_overlay()

    assert len(overlay.places) == 2
    assert overlay.lifts == 2
    assert text.cget("cursor") == "watch"

    busy.leave()
    assert text.cget("cursor") == "xterm"
    busy.raise_overlay()
    assert len(overlay.places) == 2


def test_busy_indicator_can_enter_without_showing_overlay():
    root = FakeRoot()
    overlay = FakeOverlay()
    busy = BusyIndicator(root, overlay)

    busy.enter(show_overlay=False)
    assert busy.active
    assert root.cursors == ["watch"]
    assert overlay.places == []

    busy.leave()
    assert overlay.hidden == 0
    assert root.cursors == ["watch", ""]


def test_busy_indicator_accepts_label_alias():
    root = FakeRoot()
    label = FakeOverlay()
    busy = BusyIndicator(root, label=label)

    busy.enter()
    assert label.places
    busy.leave()
    assert label.hidden == 1


def test_busy_indicator_without_overlay_only_changes_cursor():
    root = FakeRoot()
    busy = BusyIndicator(root)

    busy.enter()
    busy.leave()

    assert root.cursors == ["watch", ""]
