"""Compatibilidade de importação da janela principal baseada em shell."""

from __future__ import annotations

from b3_selic_pre.presentation.gui.selic_pre_tab import SelicPreTab
from b3_selic_pre.presentation.gui.shell import AppShell

SelicPreApp = AppShell

__all__ = ["AppShell", "SelicPreApp", "SelicPreTab"]
