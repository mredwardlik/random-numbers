import random

import pytest

from random_numbers import complex_events, conditional_events, group_events, simple_events, to_probabilities


def rng():
    return random.Random(2021)


def test_simple_events():
    result = simple_events(0.2, 10_000, rng())
    assert result.counts['A'] + result.counts['!A'] == 10_000
    assert result.frequency('A') == pytest.approx(0.2, abs=0.015)
    assert result.probabilities == {'A': 0.2, '!A': 0.8}


def test_seed_reproducibility():
    assert simple_events(0.3, 100, rng()).counts == simple_events(0.3, 100, rng()).counts


@pytest.mark.parametrize('p1, p2, outcome', [(1, 1, 'AB'), (1, 0, 'A!B'), (0, 1, '!AB'), (0, 0, '!A!B')])
def test_complex_events_labels(p1, p2, outcome):
    # the old version printed the counts under wrong headers
    assert complex_events(p1, p2, 50).counts[outcome] == 50


def test_complex_events_frequencies():
    result = complex_events(0.15, 0.2, 100_000, rng())
    assert sum(result.probabilities.values()) == pytest.approx(1)
    for outcome, p in result.probabilities.items():
        assert result.frequency(outcome) == pytest.approx(p, abs=0.01)


@pytest.mark.parametrize('pa, pb_a, pb_not_a, outcome', [
    (1, 1, 0, 'AB'), (1, 0, 1, 'A!B'), (0, 0, 1, '!AB'), (0, 1, 0, '!A!B'),
])
def test_conditional_events_labels(pa, pb_a, pb_not_a, outcome):
    assert conditional_events(pa, pb_a, pb_not_a, 50).counts[outcome] == 50


def test_conditional_events_frequencies():
    result = conditional_events(0.6, 0.5, 0.75, 100_000, rng())
    assert result.probabilities == pytest.approx({'AB': 0.3, 'A!B': 0.3, '!AB': 0.3, '!A!B': 0.1})
    for outcome, p in result.probabilities.items():
        assert result.frequency(outcome) == pytest.approx(p, abs=0.01)


def test_group_events():
    result = group_events([0.1, 0.2, 0.3, 0.4], 100_000, rng())
    assert result.outcomes == ['A1', 'A2', 'A3', 'A4']
    assert sum(result.counts.values()) == 100_000
    for outcome, p in result.probabilities.items():
        assert result.frequency(outcome) == pytest.approx(p, abs=0.01)


def test_group_events_rounding_of_sum():
    # 0.1 + 0.2 + 0.3 + 0.4 = 1.0000000000000002 and 0.7 + 0.1 + 0.1 + 0.1 = 0.9999999999999999
    class Top(random.Random):
        def random(self):
            return 0.99999999999999994

    assert group_events([0.7, 0.1, 0.1, 0.1], 3, Top()).counts['A4'] == 3
    assert group_events([0.5, 0.5, 0, 0], 3, Top()).counts == {'A1': 0, 'A2': 3, 'A3': 0, 'A4': 0}


def test_group_events_names():
    result = group_events([0.5, 0.5], 10, names=['орёл', 'решка'])
    assert set(result.counts) == {'орёл', 'решка'}


@pytest.mark.parametrize('probabilities', [[1], [0.5, 0.4], [0.5, 0.6], [1.5, -0.5]])
def test_group_events_invalid(probabilities):
    with pytest.raises(ValueError):
        group_events(probabilities, 10)


def test_to_probabilities():
    assert to_probabilities([40, 60, 30, 20]) == pytest.approx([4 / 15, 0.4, 0.2, 2 / 15])
    with pytest.raises(ValueError):
        to_probabilities([0, 0])


@pytest.mark.parametrize('p, n', [(-0.1, 10), (1.1, 10), (0.5, 0), (0.5, 2.5)])
def test_invalid_parameters(p, n):
    with pytest.raises(ValueError):
        simple_events(p, n)
