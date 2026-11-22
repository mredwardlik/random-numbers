import math
import random
import statistics

import pytest

from random_numbers import (geometric_probabilities, geometric_sample, inverse_transform, neumann, normal_clt,
                            poisson_probabilities, poisson_probability, poisson_process, poisson_sample)
from random_numbers.distributions import density_moments


def rng():
    return random.Random(7)


def test_geometric_probabilities():
    assert geometric_probabilities(0.23, 3) == pytest.approx([0.23, 0.1771, 0.136367])
    assert sum(geometric_probabilities(0.5, 60)) == pytest.approx(1)


def test_geometric_sample():
    sample = geometric_sample(0.25, 20_000, rng())
    assert min(sample) == 1
    assert statistics.fmean(sample) == pytest.approx(4, rel=0.03)
    assert sample.count(1) / len(sample) == pytest.approx(0.25, abs=0.01)
    assert geometric_sample(1, 5) == [1] * 5


def test_poisson_probabilities():
    probabilities = poisson_probabilities(8, 60)
    assert sum(probabilities) == pytest.approx(1)
    assert probabilities[8] == pytest.approx(8 ** 8 * math.exp(-8) / math.factorial(8))


def test_poisson_large_lambda_does_not_overflow():
    # the old version computed λ^k and k! directly and failed with OverflowError
    assert poisson_probability(800, 800) == pytest.approx(1 / math.sqrt(2 * math.pi * 800), rel=1e-3)


def test_poisson_sample():
    sample = poisson_sample(8, 20_000, rng())
    assert statistics.fmean(sample) == pytest.approx(8, rel=0.02)
    assert statistics.pvariance(sample) == pytest.approx(8, rel=0.06)


def test_poisson_process():
    times = poisson_process(1 / 3, 100, rng())
    assert times == sorted(times)
    assert all(0 < t <= 100 for t in times)


def test_poisson_process_rate_above_one():
    # the old version stopped after t events, so with λ = 5 and t = 10 there were at most 10 instead of ~50
    counts = [len(poisson_process(5, 10, random.Random(seed))) for seed in range(200)]
    assert statistics.fmean(counts) == pytest.approx(50, rel=0.05)


def test_normal_clt():
    sample = normal_clt(5, 2, 20_000, rng())
    assert statistics.fmean(sample) == pytest.approx(5, abs=0.05)
    assert statistics.pstdev(sample) == pytest.approx(2, rel=0.03)  # σ, not the variance
    assert all(5 - 12 <= x <= 5 + 12 for x in sample)


def test_inverse_transform_exponential():
    sample = inverse_transform(lambda z: -math.log(1 - z) / 2, 20_000, rng())
    assert statistics.fmean(sample) == pytest.approx(0.5, rel=0.03)
    assert min(sample) > 0


def test_inverse_transform_bad_function():
    with pytest.raises(ValueError):
        inverse_transform(lambda z: math.log(z - 2), 10)


def test_neumann_matches_density():
    density = lambda x: 2 * x + x ** 4  # noqa: E731
    result = neumann(density, 1, 5, 20_000, rng())
    mean, variance = density_moments(density, 1, 5)
    assert all(1 <= x <= 5 for x in result.x)
    assert statistics.fmean(result.x) == pytest.approx(mean, rel=0.01)
    assert statistics.pvariance(result.x) == pytest.approx(variance, rel=0.05)
    assert 0 < result.acceptance < 1
    assert all(y < density(x) for x, y in zip(result.x, result.y))


def test_neumann_height_too_small():
    with pytest.raises(ValueError, match='увеличьте M'):
        neumann(lambda x: x, 0, 1, 100, rng(), height=0.5)


@pytest.mark.parametrize('density, a, b', [(lambda x: x - 1, 0, 2), (lambda x: 0, 0, 1), (lambda x: x, 2, 1)])
def test_neumann_invalid(density, a, b):
    with pytest.raises(ValueError):
        neumann(density, a, b, 10)


@pytest.mark.parametrize('call', [
    lambda: geometric_probabilities(0, 5),
    lambda: poisson_sample(0, 5),
    lambda: poisson_process(1, 0),
    lambda: normal_clt(0, -1, 5),
    lambda: geometric_sample(0.5, 0),
])
def test_invalid_parameters(call):
    with pytest.raises(ValueError):
        call()
