"""Domain models for b3_selic_pre."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RateRecord:
    """SELIC reference rate record for a business day."""

    day252: int
    day360: int
    rate: str
