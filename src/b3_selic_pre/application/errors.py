"""Erros de contrato compartilhados pela camada de aplicação."""

from __future__ import annotations


class CommunicationError(Exception):
    """Falha prevista de comunicação com um serviço externo."""
