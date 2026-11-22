"""Pseudo-random number generators: deterministic sequences on ``[0, 1)``.

Every generator is an iterator of floats and keeps a small immutable state, so
the period of its sequence can be found exactly (see :meth:`Generator.period`).

>>> MiddleSquare('0.8933').take(3)
[0.7984, 0.7442, 0.3833]
>>> LinearCongruential(7, a=21, c=17, m=100).take(3)
[0.64, 0.61, 0.98]
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Hashable, Iterator, NamedTuple, Sequence

DEFAULT_PERIOD_LIMIT = 200_000


class Period(NamedTuple):
    """The cycle of a sequence: it repeats with period ``length`` after ``start`` numbers.

    ``aperiodic`` is the length of the aperiodic segment: how many numbers come
    before the first repetition.
    """

    start: int
    length: int

    @property
    def aperiodic(self) -> int:
        return self.start + self.length


def _decimal(value: str | int | float | Decimal, name: str) -> Decimal:
    try:
        number = Decimal(str(value).strip().replace(',', '.'))
    except InvalidOperation:
        raise ValueError(f'{name}: «{value}» — не число.') from None
    if not number.is_finite():
        raise ValueError(f'{name}: нужно конечное число.')
    return number


def _check_count(n: int) -> None:
    if not isinstance(n, int) or n < 0:
        raise ValueError('Количество чисел должно быть целым и не меньше 0.')


class Generator(ABC, Iterator[float]):
    """Base class: an infinite iterator of numbers in ``[0, 1)``."""

    value: float

    @abstractmethod
    def _step(self) -> None:
        """Move to the next state and update ``value``."""

    @property
    @abstractmethod
    def state(self) -> Hashable:
        """Everything the next numbers depend on."""

    def __next__(self) -> float:
        self._step()
        return self.value

    def take(self, n: int) -> list[float]:
        """The next ``n`` numbers."""
        _check_count(n)
        return [next(self) for _ in range(n)]

    def copy(self):
        return copy.copy(self)

    def period(self, limit: int = DEFAULT_PERIOD_LIMIT) -> Period | None:
        """Find the cycle of the sequence from the current state (Brent's algorithm).

        Returns ``None`` if the sequence does not repeat within ``limit`` numbers.
        The generator itself is not moved.
        """
        power = length = 1
        tortoise, hare = self.copy(), self.copy()
        hare._step()
        steps = 1
        while tortoise.state != hare.state:
            if steps >= limit:
                return None
            if power == length:
                tortoise, power, length = hare.copy(), power * 2, 0
            hare._step()
            length += 1
            steps += 1
        tortoise, hare = self.copy(), self.copy()
        for _ in range(length):
            hare._step()
        start = 0
        while tortoise.state != hare.state:
            tortoise._step()
            hare._step()
            start += 1
        return Period(start, length)


class MiddleSquare(Generator):
    """Middle-square method (von Neumann): the next number is the middle ``k`` digits of the square.

    The seed sets the number of digits ``k``: ``'0.8933'`` and ``5735`` both give
    ``k = 4``. Pass the seed as a string to keep trailing zeros (``'0.8930'``).
    For an odd ``k`` the square is cut ``k // 2`` digits from the right.

    >>> MiddleSquare(5735).take(4)
    [0.8902, 0.2456, 0.0319, 0.1017]
    >>> MiddleSquare('0.0010').take(3)  # degenerates to zero
    [0.0001, 0.0, 0.0]
    """

    def __init__(self, seed: str | int | float | Decimal, digits: int | None = None):
        number = _decimal(seed, 'Начальное значение')
        if number < 0:
            raise ValueError('Начальное значение должно быть неотрицательным.')
        if number < 1:
            exponent = number.as_tuple().exponent
            k = -exponent if isinstance(exponent, int) and exponent < 0 else 0
            z = int(number.scaleb(k))
        else:
            if number != number.to_integral_value():
                raise ValueError('Начальное значение: целое число (5735) или дробь от 0 до 1 (0.5735).')
            z = int(number)
            k = len(str(z))
        if digits is not None:
            if digits < len(str(z)) and z:
                raise ValueError(f'В начальном значении больше {digits} цифр.')
            k = digits
        if k < 2:
            raise ValueError('В начальном значении нужно хотя бы 2 цифры.')
        self.digits = k
        self.z = z
        self.value = z / 10 ** k

    def _step(self) -> None:
        k = self.digits
        self.z = self.z * self.z // 10 ** (k // 2) % 10 ** k
        self.value = self.z / 10 ** k

    @property
    def state(self) -> int:
        return self.z


class LinearCongruential(Generator):
    """Linear congruential generator: ``z[i+1] = (a·z[i] + c) mod m``, ``r = z / m``.

    The integer ``z`` of the last number is in the ``z`` attribute.

    >>> g = LinearCongruential(7, a=7, c=7, m=8)
    >>> [(next(g), g.z) for _ in range(3)]
    [(0.0, 0), (0.875, 7), (0.0, 0)]
    """

    def __init__(self, seed: int, *, a: int, c: int, m: int):
        for name, value in (('z₀', seed), ('a', a), ('c', c), ('m', m)):
            if not isinstance(value, int):
                raise ValueError(f'{name} должно быть целым числом.')
        if m < 2:
            raise ValueError('Модуль m должен быть не меньше 2.')
        if not 0 < a < m:
            raise ValueError('Множитель a должен быть в диапазоне 1 … m − 1.')
        if not 0 <= c < m:
            raise ValueError('Приращение c должно быть в диапазоне 0 … m − 1.')
        if not 0 <= seed < m:
            raise ValueError('Начальное значение z₀ должно быть в диапазоне 0 … m − 1.')
        self.a, self.c, self.m = a, c, m
        self.z = seed
        self.value = seed / m

    def _step(self) -> None:
        self.z = (self.a * self.z + self.c) % self.m
        self.value = self.z / self.m

    @property
    def state(self) -> int:
        return self.z


class Davis(Generator):
    """Davis additive method: ``z[i] = (z[i-1] + z[i-k]) mod m``, ``r = z / m``.

    ``k`` is the number of seeds (at least 2). Seeds and the modulus can be
    fractions: with ``m = 1`` the method adds the fractional parts. The math is
    done in decimals, so ``0.36 + 0.62`` is exactly ``0.98``.

    >>> Davis(['0.36', '0.45', '0.62'], m=1).take(4)
    [0.98, 0.43, 0.05, 0.03]
    """

    def __init__(self, seeds: Sequence[str | int | float | Decimal], m: str | int | float | Decimal = 1):
        if len(seeds) < 2:
            raise ValueError('Нужно хотя бы 2 начальных значения.')
        self.m = _decimal(m, 'Модуль')
        if self.m <= 0:
            raise ValueError('Модуль m должен быть больше 0.')
        window = tuple(_decimal(seed, 'Начальное значение') for seed in seeds)
        if any(not 0 <= seed < self.m for seed in window):
            raise ValueError('Начальные значения должны быть в диапазоне [0, m).')
        self.window = window
        self.value = float(window[-1] / self.m)

    def _step(self) -> None:
        z = (self.window[-1] + self.window[0]) % self.m
        self.window = self.window[1:] + (z,)
        self.value = float(z / self.m)

    @property
    def state(self) -> tuple[Decimal, ...]:
        return self.window


class Golenko(Generator):
    """Golenko perturbation method: a linear congruential sequence where every
    ``period``-th number is replaced by the middle ``digits`` digits of the square
    of the previous one. The perturbation breaks short cycles of the LCG.

    >>> numbers = Golenko(120, a=302, c=4965, m=42782, period=5).take(6)
    >>> round(numbers[3], 4), numbers[4]  # the 5th number is the middle of 5962² = 35545444
    (0.5962, 0.5454)
    """

    def __init__(self, seed: int, *, a: int, c: int, m: int, period: int, digits: int = 4):
        self._lcg = LinearCongruential(seed, a=a, c=c, m=m)
        if not isinstance(period, int) or period < 2:
            raise ValueError('Период возмущений должен быть целым и не меньше 2.')
        if not isinstance(digits, int) or digits < 2:
            raise ValueError('Число разрядов должно быть целым и не меньше 2.')
        self.period_of_perturbation = period
        self.digits = digits
        self.phase = 0
        self._r = Fraction(seed, m)
        self.value = float(self._r)

    def _step(self) -> None:
        self.phase = (self.phase + 1) % self.period_of_perturbation
        lcg = self._lcg
        if self.phase == 0:
            k = self.digits
            z = int(self._r * 10 ** k)
            z = z * z // 10 ** (k // 2) % 10 ** k
            self._r = Fraction(z, 10 ** k)
            lcg.z = int(self._r * lcg.m)
        else:
            lcg._step()
            self._r = Fraction(lcg.z, lcg.m)
        self.value = float(self._r)

    @property
    def state(self) -> tuple[int, int]:
        return self._lcg.z, self.phase

    def copy(self):
        clone = copy.copy(self)
        clone._lcg = self._lcg.copy()
        return clone


def middle_square(seed: str | int | float | Decimal, n: int, digits: int | None = None) -> list[float]:
    """``n`` numbers of the middle-square method, see :class:`MiddleSquare`."""
    return MiddleSquare(seed, digits).take(n)


def lcg(seed: int, n: int, *, a: int, c: int, m: int) -> list[int]:
    """``n`` integers of the linear congruential method (divide by ``m`` to get ``[0, 1)``).

    >>> lcg(7, 3, a=7, c=7, m=8)
    [0, 7, 0]
    """
    generator = LinearCongruential(seed, a=a, c=c, m=m)
    _check_count(n)
    result = []
    for _ in range(n):
        next(generator)
        result.append(generator.z)
    return result


def davis(seeds: Sequence[str | int | float | Decimal], n: int, m: str | int | float | Decimal = 1) -> list[float]:
    """``n`` numbers of the Davis additive method, see :class:`Davis`."""
    return Davis(seeds, m).take(n)


def golenko(seed: int, n: int, *, a: int, c: int, m: int, period: int, digits: int = 4) -> list[float]:
    """``n`` numbers of the Golenko perturbation method, see :class:`Golenko`."""
    return Golenko(seed, a=a, c=c, m=m, period=period, digits=digits).take(n)
