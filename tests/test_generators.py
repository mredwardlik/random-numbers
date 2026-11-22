import pytest

from random_numbers import Davis, Golenko, LinearCongruential, MiddleSquare, davis, golenko, lcg, middle_square


class TestMiddleSquare:
    def test_textbook_sequence(self):
        assert middle_square('0.8933', 3) == [0.7984, 0.7442, 0.3833]

    def test_integer_seed(self):
        assert middle_square(5735, 2) == [0.8902, 0.2456]

    def test_keeps_number_of_digits_with_leading_zeros(self):
        # 0.0319² = 0.00101761 -> the middle 4 digits are 1017, not 101 or 0
        generator = MiddleSquare('0.0319')
        assert generator.digits == 4
        assert next(generator) == 0.1017
        assert generator.digits == 4

    def test_trailing_zero_counts_as_digit(self):
        assert MiddleSquare('0.8930').digits == 4
        assert MiddleSquare(0.893).digits == 3

    def test_comma_decimal_separator(self):
        assert middle_square('0,8933', 1) == [0.7984]

    def test_odd_number_of_digits(self):
        # 12345² = 0152399025 -> drop 2 digits on the right, keep 5
        assert middle_square(12345, 1) == [0.23990]

    def test_explicit_digits(self):
        assert MiddleSquare(42, digits=4).digits == 4
        with pytest.raises(ValueError):
            MiddleSquare(12345, digits=4)

    def test_degenerates_to_zero(self):
        generator = MiddleSquare('0.0010')
        assert generator.take(3) == [0.0001, 0.0, 0.0]
        assert generator.period().length == 1

    @pytest.mark.parametrize('seed', ['-0.5', '12.5', 'abc', '7', '0.5', 'inf'])
    def test_invalid_seed(self, seed):
        with pytest.raises(ValueError):
            MiddleSquare(seed)

    def test_period(self):
        period = MiddleSquare('0.8933').period()
        assert (period.start, period.length, period.aperiodic) == (25, 4, 29)
        values = middle_square('0.8933', 40)
        assert values[28] == values[24]
        assert len(set(values[:28])) == 28


class TestLinearCongruential:
    def test_small_example(self):
        assert lcg(7, 3, a=7, c=7, m=8) == [0, 7, 0]

    def test_uniform_values(self):
        assert LinearCongruential(7, a=21, c=17, m=100).take(3) == [0.64, 0.61, 0.98]

    def test_full_period(self):
        # Hull-Dobell: c coprime with m, a - 1 divisible by every prime factor of m and by 4
        period = LinearCongruential(7, a=21, c=17, m=100).period()
        assert (period.start, period.length) == (0, 100)
        assert sorted(lcg(7, 100, a=21, c=17, m=100)) == list(range(100))

    def test_short_period(self):
        assert LinearCongruential(7, a=7, c=7, m=8).period().length == 2

    def test_period_does_not_move_generator(self):
        generator = LinearCongruential(7, a=21, c=17, m=100)
        generator.period()
        assert next(generator) == 0.64

    def test_long_period_hits_limit(self):
        assert LinearCongruential(1, a=16807, c=0, m=2 ** 31 - 1).period(limit=1000) is None

    @pytest.mark.parametrize('kwargs', [
        dict(seed=1, a=0, c=1, m=10),
        dict(seed=1, a=10, c=1, m=10),
        dict(seed=10, a=3, c=1, m=10),
        dict(seed=1, a=3, c=-1, m=10),
        dict(seed=1, a=3, c=1, m=1),
        dict(seed=1.5, a=3, c=1, m=10),
    ])
    def test_invalid_parameters(self, kwargs):
        seed = kwargs.pop('seed')
        with pytest.raises(ValueError):
            LinearCongruential(seed, **kwargs)


class TestDavis:
    def test_additive_rule_is_exact(self):
        # z3 = z2 + z0 = 0.98, z4 = (0.98 + 0.45) mod 1 = 0.43, z5 = 0.43 + 0.62 - 1 = 0.05
        assert davis(['0.36', '0.45', '0.62'], 4) == [0.98, 0.43, 0.05, 0.03]

    def test_integer_modulus(self):
        # z = (z[i-1] + z[i-2]) mod 10, the Fibonacci numbers mod 10
        assert [round(r * 10) for r in davis([1, 1], 8, m=10)] == [2, 3, 5, 8, 3, 1, 4, 5]

    def test_fibonacci_mod_10_period(self):
        assert Davis([1, 1], m=10).period().length == 60

    @pytest.mark.parametrize('seeds, m', [([0.5], 1), ([0.5, 1.5], 1), ([-0.1, 0.2], 1), ([0.1, 0.2], 0)])
    def test_invalid(self, seeds, m):
        with pytest.raises(ValueError):
            Davis(seeds, m)


class TestGolenko:
    PARAMS = dict(a=302, c=4965, m=42782, period=5)

    def test_lcg_between_perturbations(self):
        lcg_values = LinearCongruential(120, a=302, c=4965, m=42782).take(4)
        assert golenko(120, 4, **self.PARAMS) == lcg_values

    def test_every_pth_number_is_perturbed(self):
        values = golenko(120, 10, **self.PARAMS)
        z = int(values[3] * 10 ** 4)
        assert values[4] == (z * z // 100 % 10 ** 4) / 10 ** 4

    def test_perturbation_changes_lcg_course(self):
        plain = LinearCongruential(120, a=302, c=4965, m=42782).take(6)
        perturbed = golenko(120, 6, **self.PARAMS)
        assert perturbed[5] != plain[5]

    def test_period_and_copy(self):
        generator = Golenko(120, **self.PARAMS)
        period = generator.period()
        assert period is not None and period.length % 5 == 0
        assert generator.take(4) == golenko(120, 4, **self.PARAMS)

    @pytest.mark.parametrize('period, digits', [(1, 4), (5, 1)])
    def test_invalid(self, period, digits):
        with pytest.raises(ValueError):
            Golenko(120, a=302, c=4965, m=42782, period=period, digits=digits)


def test_values_are_in_unit_interval():
    for generator in (MiddleSquare('0.5735'), LinearCongruential(1, a=21, c=17, m=100),
                      Davis(['0.1', '0.7', '0.3']), Golenko(120, a=302, c=4965, m=42782, period=5)):
        assert all(0 <= value < 1 for value in generator.take(500))


def test_negative_count():
    with pytest.raises(ValueError):
        middle_square('0.8933', -1)
