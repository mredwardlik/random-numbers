import math

import pytest

from random_numbers import Function


@pytest.mark.parametrize('text, x, expected', [
    ('2*x + x^4', 2, 20),
    ('2*x + x**4', 2, 20),
    ('-x^2', 3, -9),
    ('2^3^2', 0, 512),
    ('sqrt(x) + ln(e)', 9, 4),
    ('sin(pi / 2) * exp(0)', 0, 1),
    ('max(x, 1) % 3', 7, 1),
    ('1e-3 * x', 2, 0.002),
])
def test_values(text, x, expected):
    assert Function(text)(x) == pytest.approx(expected)


def test_variable_name():
    assert Function('-ln(1 - z) / 2', 'z')(1 - math.exp(-2)) == pytest.approx(1)
    with pytest.raises(ValueError, match='Переменная — z'):
        Function('x + 1', 'z')


@pytest.mark.parametrize('text', [
    '', '2 +', '__import__("os")', 'x.real', '(lambda: 1)()', '[1, 2]', 'x if x else 1',
    '"text"', 'True', 'open("file")', 'log(x, base=2)', 'x < 1', 'a' * 400,
])
def test_rejected(text):
    with pytest.raises(ValueError):
        Function(text)


@pytest.mark.parametrize('text, x', [('1 / x', 0), ('sqrt(x)', -1), ('log(x)', 0), ('10 ^ 10000', 1), ('x ^ 0.5', -1)])
def test_evaluation_errors(text, x):
    with pytest.raises(ValueError):
        Function(text)(x)


def test_str():
    assert str(Function(' x + 1 ')) == 'x + 1'
