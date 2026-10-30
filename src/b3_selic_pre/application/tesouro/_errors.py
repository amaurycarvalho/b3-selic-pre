"""Erros de domínio da consulta de vendas do Tesouro Direto."""

from __future__ import annotations


class TesouroDataError(ValueError):
    """CSV do Tesouro inválido, incompleto ou sem registros."""


class PeriodoInvalidoError(ValueError):
    """Período de consulta inválido (datas ou ordem)."""
