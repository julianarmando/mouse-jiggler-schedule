from __future__ import annotations
import math
import random
from abc import ABC, abstractmethod


class BaseMovement(ABC):
    def reset(self) -> None:
        pass

    @abstractmethod
    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        """Returns (dx, dy) offset from the engine's stored origin point."""
        pass

    def _jitter(self, dx: float, dy: float, jitter: float) -> tuple[float, float]:
        if jitter > 0:
            dx += random.gauss(0, jitter * 3)
            dy += random.gauss(0, jitter * 3)
        return dx, dy


class MicroJiggle(BaseMovement):
    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        amp = max(1, min(amplitude, 3))
        dx = random.uniform(-amp, amp)
        dy = random.uniform(-amp, amp)
        return dx, dy


class Circular(BaseMovement):
    def __init__(self) -> None:
        self._angle = 0.0

    def reset(self) -> None:
        self._angle = 0.0

    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        self._angle = (self._angle + 0.15) % (2 * math.pi)
        dx = amplitude * math.cos(self._angle)
        dy = amplitude * math.sin(self._angle)
        return self._jitter(dx, dy, jitter)


class RandomWalk(BaseMovement):
    def __init__(self) -> None:
        self._dx = 0.0
        self._dy = 0.0

    def reset(self) -> None:
        self._dx = 0.0
        self._dy = 0.0

    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        self._dx += random.uniform(-2, 2) - self._dx * 0.1
        self._dy += random.uniform(-2, 2) - self._dy * 0.1
        self._dx = max(-amplitude, min(amplitude, self._dx))
        self._dy = max(-amplitude, min(amplitude, self._dy))
        return self._jitter(self._dx, self._dy, jitter)


class FigureEight(BaseMovement):
    def __init__(self) -> None:
        self._t = 0.0

    def reset(self) -> None:
        self._t = 0.0

    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        self._t = (self._t + 0.1) % (2 * math.pi)
        denom = 1 + math.sin(self._t) ** 2
        scale = amplitude / math.sqrt(2)
        dx = scale * math.sqrt(2) * math.cos(self._t) / denom
        dy = scale * math.sqrt(2) * math.cos(self._t) * math.sin(self._t) / denom
        return self._jitter(dx, dy, jitter)


class DiagonalBounce(BaseMovement):
    def __init__(self) -> None:
        self._pos = 0.0
        self._dir = 1.0

    def reset(self) -> None:
        self._pos = 0.0
        self._dir = 1.0

    def compute_offset(self, amplitude: int, jitter: float) -> tuple[float, float]:
        self._pos += 2.0 * self._dir
        if abs(self._pos) >= amplitude:
            self._dir *= -1
            self._pos = float(amplitude) * self._dir
        return self._jitter(self._pos, self._pos, jitter)


MOVEMENT_CLASSES: dict[str, type[BaseMovement]] = {
    "micro_jiggle": MicroJiggle,
    "circular": Circular,
    "random_walk": RandomWalk,
    "figure_eight": FigureEight,
    "diagonal_bounce": DiagonalBounce,
}

MOVEMENT_LABELS: dict[str, str] = {
    "micro_jiggle": "Micro Jiggle",
    "circular": "Circular",
    "random_walk": "Random Walk",
    "figure_eight": "Figure Eight",
    "diagonal_bounce": "Diagonal Bounce",
}


def create_movement(mode: str) -> BaseMovement:
    return MOVEMENT_CLASSES.get(mode, MicroJiggle)()