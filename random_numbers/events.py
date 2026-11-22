"""Simulation of random events with a uniform random number ``z`` on ``[0, 1)``.

An event with probability ``p`` happens when ``z < p``. Each function runs ``n``
trials and returns an :class:`Experiment`: how many times every outcome came up
next to its theoretical probability.

>>> import random
>>> result = complex_events(0.5, 0.5, 1000, rng=random.Random(1))
>>> sorted(result.counts)
['!A!B', '!AB', 'A!B', 'AB']
>>> sum(result.counts.values())
1000
"""

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass
from itertools import accumulate
from typing import Sequence

PROBABILITY_TOLERANCE = 1e-6


@dataclass(frozen=True)
class Experiment:
    """Outcome counts of ``n`` trials and the theoretical probabilities."""

    n: int
    counts: dict[str, int]
    probabilities: dict[str, float]

    @property
    def outcomes(self) -> list[str]:
        return list(self.probabilities)

    def frequency(self, outcome: str) -> float:
        """Relative frequency of an outcome: ``count / n``."""
        return self.counts[outcome] / self.n if self.n else 0.0

    @property
    def frequencies(self) -> dict[str, float]:
        return {outcome: self.frequency(outcome) for outcome in self.outcomes}


def check_probability(p: float, name: str = 'Вероятность') -> float:
    if not isinstance(p, (int, float)) or not 0 <= p <= 1:
        raise ValueError(f'{name} должна быть в диапазоне [0, 1].')
    return float(p)


def check_trials(n: int) -> int:
    if not isinstance(n, int) or n < 1:
        raise ValueError('Количество испытаний должно быть целым и не меньше 1.')
    return n


def _random(rng: random.Random | None):
    return (rng or random).random


def simple_events(p: float, n: int, rng: random.Random | None = None) -> Experiment:
    """Event ``A`` with probability ``p``: outcomes ``'A'`` and ``'!A'``.

    >>> simple_events(1, 10).counts
    {'A': 10, '!A': 0}
    """
    check_probability(p)
    check_trials(n)
    z = _random(rng)
    happened = sum(z() < p for _ in range(n))
    return Experiment(n, {'A': happened, '!A': n - happened}, {'A': p, '!A': 1 - p})


def complex_events(p1: float, p2: float, n: int, rng: random.Random | None = None) -> Experiment:
    """Two independent events: ``P(A) = p1``, ``P(B) = p2``.

    Outcomes: ``'AB'`` (both), ``'A!B'`` (only A), ``'!AB'`` (only B), ``'!A!B'`` (neither).
    """
    check_probability(p1, 'Вероятность A')
    check_probability(p2, 'Вероятность B')
    check_trials(n)
    z = _random(rng)
    counts = dict.fromkeys(('AB', 'A!B', '!AB', '!A!B'), 0)
    for _ in range(n):
        a, b = z() < p1, z() < p2
        counts[('' if a else '!') + 'A' + ('' if b else '!') + 'B'] += 1
    probabilities = {
        'AB': p1 * p2,
        'A!B': p1 * (1 - p2),
        '!AB': (1 - p1) * p2,
        '!A!B': (1 - p1) * (1 - p2),
    }
    return Experiment(n, counts, probabilities)


def conditional_events(pa: float, pb_a: float, pb_not_a: float, n: int,
                       rng: random.Random | None = None) -> Experiment:
    """Dependent events: ``P(A) = pa``, ``P(B | A) = pb_a``, ``P(B | !A) = pb_not_a``.

    Outcomes are the same as in :func:`complex_events`. The total probability of
    ``B`` is ``pa·pb_a + (1 − pa)·pb_not_a``.
    """
    check_probability(pa, 'Вероятность A')
    check_probability(pb_a, 'Вероятность B при A')
    check_probability(pb_not_a, 'Вероятность B при !A')
    check_trials(n)
    z = _random(rng)
    counts = dict.fromkeys(('AB', 'A!B', '!AB', '!A!B'), 0)
    for _ in range(n):
        a = z() < pa
        b = z() < (pb_a if a else pb_not_a)
        counts[('' if a else '!') + 'A' + ('' if b else '!') + 'B'] += 1
    probabilities = {
        'AB': pa * pb_a,
        'A!B': pa * (1 - pb_a),
        '!AB': (1 - pa) * pb_not_a,
        '!A!B': (1 - pa) * (1 - pb_not_a),
    }
    return Experiment(n, counts, probabilities)


def to_probabilities(frequencies: Sequence[float]) -> list[float]:
    """Turn observed frequencies into probabilities that sum to 1.

    >>> to_probabilities([40, 60, 30, 20])
    [0.26666666666666666, 0.4, 0.2, 0.13333333333333333]
    """
    if not frequencies or any(value < 0 for value in frequencies):
        raise ValueError('Частоты должны быть неотрицательными числами.')
    total = sum(frequencies)
    if total <= 0:
        raise ValueError('Сумма частот должна быть больше 0.')
    return [value / total for value in frequencies]


def group_events(probabilities: Sequence[float], n: int, rng: random.Random | None = None,
                 names: Sequence[str] | None = None) -> Experiment:
    """A complete group of incompatible events ``A1 … Ak``: exactly one happens in every trial.

    The probabilities must sum to 1. Event ``i`` happens when ``z`` falls into
    the ``i``-th segment of ``[0, 1)`` of length ``p[i]``.

    >>> group_events([0.5, 0.5, 0], 10, names=['x', 'y', 'z']).counts['z']
    0
    """
    if len(probabilities) < 2:
        raise ValueError('Нужно хотя бы 2 события.')
    for i, p in enumerate(probabilities, 1):
        check_probability(p, f'Вероятность события {i}')
    total = math.fsum(probabilities)
    if abs(total - 1) > PROBABILITY_TOLERANCE:
        raise ValueError(f'Сумма вероятностей равна {total:g}, а должна быть 1.')
    check_trials(n)
    names = list(names) if names is not None else [f'A{i}' for i in range(1, len(probabilities) + 1)]
    if len(names) != len(probabilities) or len(set(names)) != len(names):
        raise ValueError('Нужно столько же разных названий, сколько событий.')
    bounds = list(accumulate(probabilities))
    z = _random(rng)
    hits = [0] * len(probabilities)
    # the sum may be 0.9999999 because of rounding: larger z belong to the last possible event
    last = max(i for i, p in enumerate(probabilities) if p > 0)
    for _ in range(n):
        hits[min(bisect.bisect_right(bounds, z()), last)] += 1
    return Experiment(n, dict(zip(names, hits)), dict(zip(names, map(float, probabilities))))
