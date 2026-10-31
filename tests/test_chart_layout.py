"""Testes do hardening de layout e do registro de avisos do matplotlib."""

import logging
import warnings

import pytest

from b3_selic_pre.presentation.chart_layout import apply_tight_layout


class FakeFigure:
    def __init__(self, message=None, error=None):
        self.message = message
        self.error = error
        self.pad = None
        self.adjusted = None

    def tight_layout(self, pad=None):
        self.pad = pad
        if self.error is not None:
            raise self.error
        if self.message is not None:
            warnings.warn(self.message, UserWarning)

    def subplots_adjust(self, **kwargs):
        self.adjusted = kwargs


def test_tight_layout_warning_is_logged_and_fallback_is_applied(caplog):
    figure = FakeFigure("Tight layout not applied. margins")

    with caplog.at_level(logging.WARNING):
        apply_tight_layout(figure, context="render_gap: Gap")

    assert "Tight layout não aplicado em render_gap: Gap" in caplog.text
    assert "Tight layout not applied" in caplog.text
    assert "margens conservadoras" in caplog.text
    assert figure.adjusted == {
        "left": 0.14,
        "right": 0.94,
        "top": 0.90,
        "bottom": 0.22,
    }


def test_tight_layout_passes_padding_through():
    figure = FakeFigure()

    apply_tight_layout(figure, pad=0.4)

    assert figure.pad == 0.4
    assert figure.adjusted is None


def test_unrelated_warning_is_reemitted_without_fallback():
    figure = FakeFigure("outro aviso")

    with pytest.warns(UserWarning, match="outro aviso"):
        apply_tight_layout(figure)

    assert figure.adjusted is None


def test_layout_exception_is_logged_and_fallback_is_applied(caplog):
    figure = FakeFigure(error=RuntimeError("falha de layout"))

    with caplog.at_level(logging.ERROR):
        apply_tight_layout(figure, context="render_evolution")

    assert "Falha ao aplicar tight_layout em render_evolution" in caplog.text
    assert caplog.records[-1].exc_info is not None
    assert figure.adjusted is not None


def test_missing_subplots_adjust_does_not_break_layout(caplog):
    class MinimalFigure:
        def tight_layout(self, pad=None):
            warnings.warn("Tight layout not applied", UserWarning)

    with caplog.at_level(logging.WARNING):
        apply_tight_layout(MinimalFigure(), context="minimal")

    assert "Tight layout não aplicado em minimal" in caplog.text
    assert "Falha ao aplicar margens de fallback em minimal" in caplog.text
