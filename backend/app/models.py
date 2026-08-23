"""Core domain entities for the road network."""
from dataclasses import dataclass

# Preset congestion multipliers. effective_time = base_time * congestion_multiplier
CONGESTION_LEVELS = {
    "normal": 1.0,
    "light": 1.2,
    "moderate": 1.5,
    "heavy": 2.0,
    "severe": 3.0,
}


@dataclass
class Node:
    id: int
    x: float
    y: float


@dataclass
class Road:
    source: int
    destination: int
    distance: float  # positive distance unit (e.g. km)
    speed: float  # base speed limit, same distance unit per hour
    congestion_multiplier: float = 1.0
    is_open: bool = True

    def __post_init__(self):
        if self.distance <= 0:
            raise ValueError("Road distance must be positive")
        if self.speed <= 0:
            raise ValueError("Road speed must be positive")
        if self.congestion_multiplier <= 0:
            raise ValueError("Congestion multiplier must be positive")

    @property
    def base_time(self) -> float:
        return self.distance / self.speed

    @property
    def effective_time(self) -> float:
        return self.base_time * self.congestion_multiplier
