"""Sample statistics used by the menu and the examples.

>>> describe([1, 2, 3, 4])
Summary(count=4, mean=2.5, variance=1.25, minimum=1, maximum=4)
>>> histogram([0.1, 0.2, 0.25, 0.9], bins=2, low=0, high=1)
[(0.0, 0.5, 3), (0.5, 1.0, 1)]
"""

from __future__ import annotations

import math
from collections import Counter
from typing import NamedTuple, Sequence


class Summary(NamedTuple):
    count: int
    mean: float
    variance: float
    minimum: float
    maximum: float

    @property
    def deviation(self) -> float:
        return math.sqrt(self.variance)


def describe(values: Sequence[float]) -> Summary:
    """Count, mean, variance (population), minimum and maximum of a nonempty sample."""
    if not values:
        raise ValueError('Пустая выборка.')
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / len(values)
    return Summary(len(values), mean, variance, min(values), max(values))


def histogram(values: Sequence[float], bins: int = 10, low: float | None = None,
              high: float | None = None) -> list[tuple[float, float, int]]:
    """Split ``[low, high]`` into equal bins and count the values in every bin: ``(left, right, count)``.

    Values outside the range are not counted. The last bin includes its right end.
    """
    if bins < 1:
        raise ValueError('Нужен хотя бы 1 интервал.')
    low = min(values) if low is None else low
    high = max(values) if high is None else high
    if high <= low:
        high = low + 1
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        if low <= value <= high:
            counts[min(int((value - low) / width), bins - 1)] += 1
    return [(low + i * width, low + (i + 1) * width, counts[i]) for i in range(bins)]


def nice_range(low: float, high: float, bins: int = 10) -> tuple[float, float, int]:
    """Round bounds and at most about ``bins`` bins with a step of 1, 2, 2.5 or 5 × 10ⁿ.

    >>> nice_range(2.2, 8.1, 12)
    (2.0, 8.5, 13)
    >>> nice_range(0.00014, 3.63)
    (0.0, 4.0, 8)
    """
    if high <= low:
        return low, low + 1, 1
    raw = (high - low) / bins
    power = 10 ** math.floor(math.log10(raw))
    step = next(m * power for m in (1, 2, 2.5, 5, 10) if m * power >= raw)
    start = math.floor(low / step) * step
    count = max(1, math.ceil((high - start) / step - 1e-9))
    return round(start, 12), round(start + count * step, 12), count


def frequencies(values: Sequence[int]) -> Counter:
    """How many times every value occurs."""
    return Counter(values)
