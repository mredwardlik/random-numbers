import pytest

from random_numbers.ui import fmt, integer, probability, real, reals, split_numbers


@pytest.mark.parametrize('text, expected', [('0.14', 0.14), ('0,14', 0.14), ('8/24', 1 / 3), (' 1e-6 ', 1e-6), ('-2', -2)])
def test_real(text, expected):
    assert real()(text) == pytest.approx(expected)


@pytest.mark.parametrize('text', ['abc', '1/0', '', 'inf', '1/2/3'])
def test_real_invalid(text):
    with pytest.raises(ValueError):
        real()(text)


def test_bounds():
    assert real(above=0)('0.5') == 0.5
    with pytest.raises(ValueError, match='больше 0'):
        real(above=0)('0')
    with pytest.raises(ValueError, match='не больше 14'):
        integer(0, 14)('15')
    with pytest.raises(ValueError, match='целое'):
        integer()('2.5')
    assert integer()('10 000') == 10000


def test_probability():
    assert probability('0,5') == 0.5
    with pytest.raises(ValueError):
        probability('1.2')


@pytest.mark.parametrize('text, expected', [
    ('0.1 0.2 0.3 0.4', [0.1, 0.2, 0.3, 0.4]),
    ('0.1, 0.2, 0.3', [0.1, 0.2, 0.3]),
    ('0,1 0,2', [0.1, 0.2]),
    ('40;60;30', [40, 60, 30]),
    ('40,60,30', [40, 60, 30]),
])
def test_reals(text, expected):
    assert reals()(text) == pytest.approx(expected)


def test_reals_count_and_minimum():
    with pytest.raises(ValueError):
        reals(2)('0.5')
    with pytest.raises(ValueError):
        reals(1, 0)('0.5 -1')


def test_split_numbers():
    assert split_numbers('0.1, 0.2 0,3;0.4') == ['0.1', '0.2', '0,3', '0.4']


def test_fmt():
    assert [fmt(0.7984), fmt(2.0), fmt(7), fmt(0.0)] == ['0.7984', '2', '7', '0']
