import pytest

from b3_selic_pre.presentation.tabs import LazyTabRegistry, TabSpec


def test_registry_preserves_order_and_builds_lazily():
    calls = []
    registry = LazyTabRegistry(
        [
            TabSpec("selic-pre", "SELIC Pré", lambda: calls.append("selic") or 1),
            TabSpec(
                "tesouro-direto",
                "Tesouro Direto",
                lambda: calls.append("tesouro") or 2,
            ),
        ]
    )

    assert [spec.tab_id for spec in registry.ordered_specs()] == [
        "selic-pre",
        "tesouro-direto",
    ]
    assert not registry.is_built("selic-pre")
    assert registry.ensure_built("selic-pre") == 1
    assert registry.ensure_built("selic-pre") == 1
    assert calls == ["selic"]
    assert registry.built_ids() == ("selic-pre",)


def test_ensure_built_is_idempotent_and_mark_visible_records_tab():
    calls = []
    registry = LazyTabRegistry(
        [TabSpec("estoque", "Estoque", lambda: calls.append("build") or object())]
    )

    first = registry.mark_visible("estoque")
    second = registry.mark_visible("estoque")

    assert first is second
    assert calls == ["build"]
    assert registry.visible_id == "estoque"


def test_duplicate_identifier_is_rejected():
    registry = LazyTabRegistry([TabSpec("a", "A", object)])

    with pytest.raises(ValueError):
        registry.register(TabSpec("a", "Outra", object))


def test_cambio_is_absent_until_registered():
    registry = LazyTabRegistry([TabSpec("selic-pre", "SELIC Pré", object)])

    assert "cambio" not in {spec.tab_id for spec in registry.ordered_specs()}


def test_unknown_tab_raises_key_error():
    registry = LazyTabRegistry()

    with pytest.raises(KeyError):
        registry.ensure_built("missing")
