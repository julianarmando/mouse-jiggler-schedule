from __future__ import annotations
import math
import random
from abc import ABC, abstractmethod


class BaseMovement(ABC):
    def reset(self) -> None:
        pass

    @abstractmethod
    def get_path(self, amplitude: int, jitter: float) -> list[tuple[float, float]]:
        """Returns a list of (dx, dy) offsets from origin for one animation cycle.
        The last point must be (0.0, 0.0) so the cursor returns to its start position.
        """
        pass


class Loop(BaseMovement):
    """Smooth circular loop. Cursor leaves origin, traces a full circle, returns to exact start."""

    STEPS = 40

    def get_path(self, amplitude: int, jitter: float) -> list[tuple[float, float]]:
        r = amplitude / 2.0
        path: list[tuple[float, float]] = []
        for i in range(1, self.STEPS + 1):
            # Circle centered at (0, r) with radius r.
            # At i=STEPS the angle completes 2π and returns to (0, 0).
            angle = -math.pi / 2 + 2 * math.pi * i / self.STEPS
            dx = r * math.cos(angle)
            dy = r + r * math.sin(angle)
            path.append((dx, dy))
        return path


class Zen(BaseMovement):
    """Barely visible micro-movement. Drifts a few pixels and returns to origin."""

    STEPS = 10

    def get_path(self, amplitude: int, jitter: float) -> list[tuple[float, float]]:
        amp = min(amplitude, 2)
        dx = random.uniform(-amp, amp)
        dy = random.uniform(-amp, amp)
        path: list[tuple[float, float]] = []
        for i in range(1, self.STEPS + 1):
            # Sine envelope: goes out and comes back smoothly
            t = math.sin(math.pi * i / self.STEPS)
            path.append((dx * t, dy * t))
        return path  # sin(π) = 0, so last point ≈ (0, 0)


MOVEMENT_CLASSES: dict[str, type[BaseMovement]] = {
    "loop": Loop,
    "zen": Zen,
}

MOVEMENT_LABELS: dict[str, str] = {
    "loop": "Loop",
    "zen": "Zen",
}


def create_movement(mode: str) -> BaseMovement:
    return MOVEMENT_CLASSES.get(mode, Loop)()