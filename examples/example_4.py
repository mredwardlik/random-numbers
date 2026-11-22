"""Задача 4. Метод исключения Неймана.

Смоделируйте 1000 значений случайной величины с плотностью, пропорциональной
f(x) = 2x + x⁴ на отрезке [1, 5]. Если установлен matplotlib
(pip install "random-numbers[plot]"), принятые точки показываются на графике.
"""

from statistics import fmean

from random_numbers import neumann
from random_numbers.distributions import density_moments
from random_numbers.stats import histogram

A, B, N = 1, 5, 1000


def f(x):
    return 2 * x + x ** 4


if __name__ == '__main__':
    result = neumann(f, A, B, N)
    mean, _ = density_moments(f, A, B)
    print(f'M = {result.height:.2f}, принято {N} точек из {result.attempts} '
          f'({100 * result.acceptance:.1f} %)')
    print(f'Среднее: {fmean(result.x):.4f}, теория {mean:.4f}\n')

    for left, right, count in histogram(result.x, 8, A, B):
        print(f'[{left:.1f}; {right:.1f})  {"█" * (count // 8)} {count}')

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print('\nДля графика установите matplotlib: pip install "random-numbers[plot]"')
    else:
        xs = [A + (B - A) * i / 200 for i in range(201)]
        plt.plot(xs, [f(x) for x in xs], label='f(x) = 2x + x⁴')
        plt.plot(result.x, result.y, 'o', ms=2, label='принятые точки')
        plt.axhline(result.height, color='gray', linestyle='--', label='M')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.title('Метод исключения Неймана')
        plt.legend()
        plt.show()
