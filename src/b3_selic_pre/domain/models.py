from dataclasses import dataclass


@dataclass(frozen=True)
class RateRecord:
    day252: int
    day360: int
    rate: str
