"""Discrete and continuous random variables: theoretical probabilities and sampling.

>>> geometric_probabilities(0.5, 3)
[0.5, 0.25, 0.125]
>>> round(sum(poisson_probabilities(8, 60)), 12)
1.0
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable

from .events import check_probability

GRID_POINTS = 1000
HEIGHT_MARGIN = 1.05


def _check_count(n: int, name: str = 'Количество значений') -> int:
    if not isinstance(n, int) or n < 1:
        raise ValueError(f'{name} должно быть целым и не меньше 1.')
    return n


def _open_uniform(rng: random.Random | None) -> float:
    """A uniform number in ``(0, 1)``: safe for ``log(z)`` and ``log(1 - z)``."""
    z = 0.0
    while z == 0.0:
        z = (rng or random).random()
    return z


def _check_geometric(p: float) -> float:
    check_probability(p)
    if p == 0:
        raise ValueError('Вероятность успеха должна быть больше 0.')
    return p


def geometric_probabilities(p: float, n: int) -> list[float]:
    """``P(X = k) = (1 − p)^(k−1) · p`` for ``k = 1 … n``: the first success on trial ``k``."""
    _check_geometric(p)
    _check_count(n)
    return [(1 - p) ** (k - 1) * p for k in range(1, n + 1)]


def geometric_sample(p: float, n: int, rng: random.Random | None = None) -> list[int]:
    """``n`` values of the geometric distribution, inverse transform: ``X = ⌊ln z / ln(1 − p)⌋ + 1``."""
    _check_geometric(p)
    _check_count(n)
    if p == 1:
        return [1] * n
    log_q = math.log1p(-p)
    return [int(math.log(_open_uniform(rng)) / log_q) + 1 for _ in range(n)]


def _check_lambda(lam: float) -> float:
    if not isinstance(lam, (int, float)) or not 0 < lam < math.inf:
        raise ValueError('Параметр λ должен быть больше 0.')
    return lam


def poisson_probability(lam: float, k: int) -> float:
    """``P(X = k) = λ^k · e^(−λ) / k!``, computed in logarithms, so large ``λ`` and ``k`` do not overflow.

    >>> round(poisson_probability(8, 8), 6)
    0.139587
    >>> poisson_probability(1000, 1000) > 0
    True
    """
    _check_lambda(lam)
    if k < 0:
        return 0.0
    return math.exp(k * math.log(lam) - lam - math.lgamma(k + 1))


def poisson_probabilities(lam: float, k_max: int) -> list[float]:
    """``P(X = k)`` for ``k = 0 … k_max``."""
    _check_lambda(lam)
    return [poisson_probability(lam, k) for k in range(k_max + 1)]


def poisson_sample(lam: float, n: int, rng: random.Random | None = None) -> list[int]:
    """``n`` values of the Poisson distribution, inverse transform over the cumulative probabilities."""
    _check_lambda(lam)
    _check_count(n)
    cap = int(lam + 40 * math.sqrt(lam) + 40)
    sample = []
    for _ in range(n):
        z, k, cumulative = _open_uniform(rng), 0, 0.0
        while True:
            cumulative += poisson_probability(lam, k)
            if z <= cumulative or k >= cap:
                break
            k += 1
        sample.append(k)
    return sample


def poisson_process(lam: float, t: float, rng: random.Random | None = None) -> list[float]:
    """Times of events of a Poisson process (простейший поток) with rate ``λ`` on ``(0, t]``.

    Intervals between events are exponential: ``τ = −ln z / λ``. On average
    there are ``λ·t`` events.
    """
    _check_lambda(lam)
    if not isinstance(t, (int, float)) or not 0 < t < math.inf:
        raise ValueError('Время t должно быть больше 0.')
    times, now = [], 0.0
    while True:
        now -= math.log(_open_uniform(rng)) / lam
        if now > t:
            return times
        times.append(now)


def normal_clt(mean: float, sigma: float, n: int, rng: random.Random | None = None) -> list[float]:
    """``n`` normal values by the central limit theorem: ``x = m + σ·(z₁ + … + z₁₂ − 6)``.

    The sum of 12 uniform numbers has mean 6 and variance 1. ``sigma`` is the
    standard deviation (the variance is ``σ²``).
    """
    if not isinstance(sigma, (int, float)) or sigma < 0:
        raise ValueError('Среднеквадратическое отклонение σ должно быть не меньше 0.')
    _check_count(n)
    z = (rng or random).random
    return [mean + sigma * (math.fsum(z() for _ in range(12)) - 6) for _ in range(n)]


def inverse_transform(inverse_cdf: Callable[[float], float], n: int,
                      rng: random.Random | None = None) -> list[float]:
    """Inverse transform method: ``x = F⁻¹(z)`` for uniform ``z`` in ``(0, 1)``.

    >>> sample = inverse_transform(lambda z: -math.log(1 - z) / 2, 1000, random.Random(1))
    >>> 0.4 < sum(sample) / len(sample) < 0.6  # exponential with λ = 2 has mean 0.5
    True
    """
    _check_count(n)
    sample = []
    for _ in range(n):
        try:
            x = float(inverse_cdf(_open_uniform(rng)))
        except (ArithmeticError, ValueError) as error:
            raise ValueError(f'Функцию F⁻¹(z) не удалось вычислить: {error}.') from None
        if not math.isfinite(x):
            raise ValueError('Функция F⁻¹(z) дала бесконечное значение.')
        sample.append(x)
    return sample


@dataclass(frozen=True)
class Rejection:
    """Result of the Neumann method: accepted points ``(x, y)`` under the density."""

    x: list[float]
    y: list[float]
    attempts: int
    height: float

    @property
    def acceptance(self) -> float:
        """Share of accepted points: about ``(area under f) / (M · (b − a))``."""
        return len(self.x) / self.attempts


def _density_at(density: Callable[[float], float], x: float) -> float:
    try:
        y = float(density(x))
    except (ArithmeticError, ValueError) as error:
        raise ValueError(f'Плотность f(x) не вычисляется в точке x = {x:g}: {error}.') from None
    if not math.isfinite(y):
        raise ValueError(f'Плотность f(x) бесконечна в точке x = {x:g}.')
    if y < 0:
        raise ValueError(f'Плотность f(x) отрицательна в точке x = {x:g}.')
    return y


def density_height(density: Callable[[float], float], a: float, b: float) -> float:
    """An upper bound ``M`` of the density on ``[a, b]``: the maximum on a grid plus 5 %."""
    grid = (a + (b - a) * i / GRID_POINTS for i in range(GRID_POINTS + 1))
    top = max(_density_at(density, x) for x in grid)
    if top == 0:
        raise ValueError('Плотность f(x) равна нулю на всём отрезке.')
    return top * HEIGHT_MARGIN


def density_moments(density: Callable[[float], float], a: float, b: float,
                    steps: int = 2000) -> tuple[float, float]:
    """Mean and variance of a (possibly unnormalized) density on ``[a, b]``, Simpson's rule.

    >>> [round(value, 6) for value in density_moments(lambda x: x, 0, 1)]  # density 2x
    [0.666667, 0.055556]
    """
    h = (b - a) / steps
    total = first = second = 0.0
    for i in range(steps + 1):
        x = a + i * h
        weight = 1 if i in (0, steps) else 4 if i % 2 else 2
        y = weight * _density_at(density, x)
        total += y
        first += y * x
        second += y * x * x
    if total == 0:
        raise ValueError('Плотность f(x) равна нулю на всём отрезке.')
    mean = first / total
    return mean, max(0.0, second / total - mean * mean)


def neumann(density: Callable[[float], float], a: float, b: float, n: int,
            rng: random.Random | None = None, height: float | None = None,
            max_attempts: int | None = None) -> Rejection:
    """Neumann rejection method for a density ``f`` on ``[a, b]``, the density may be unnormalized.

    Points ``(a + z₁·(b − a), M·z₂)`` are thrown into the rectangle ``[a, b] × [0, M]``,
    and those under the curve ``y = f(x)`` are kept. ``M`` is found automatically
    when ``height`` is not given.

    >>> result = neumann(lambda x: x, 0, 1, 500, random.Random(1))
    >>> len(result.x), 0.6 < sum(result.x) / 500 < 0.73  # density 2x has mean 2/3
    (500, True)
    """
    if not (math.isfinite(a) and math.isfinite(b)) or a >= b:
        raise ValueError('Нужен отрезок [a, b] с a < b.')
    _check_count(n)
    if height is None:
        height = density_height(density, a, b)
    elif not 0 < height < math.inf:
        raise ValueError('Высота M должна быть больше 0.')
    max_attempts = max_attempts or 10_000 * n
    z = (rng or random).random
    xs, ys, attempts = [], [], 0
    while len(xs) < n:
        if attempts >= max_attempts:
            raise ValueError('Принимается слишком мало точек: проверьте f(x) и M.')
        attempts += 1
        x, y = a + z() * (b - a), height * z()
        fx = _density_at(density, x)
        if fx > height:
            raise ValueError(f'f({x:g}) = {fx:g} больше высоты M = {height:g}: увеличьте M.')
        if y < fx:
            xs.append(x)
            ys.append(y)
    return Rejection(xs, ys, attempts, height)
