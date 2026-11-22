"""Задача 3. Метод обратной функции.

Время между приходами клиентов распределено экспоненциально с интенсивностью
λ = 2 клиента в минуту: F(x) = 1 − e^(−λx). Решив уравнение F(x) = z,
получаем x = −ln(1 − z) / λ. Смоделируйте 10 интервалов и проверьте среднее
по 10 000 значениям (теоретическое среднее 1 / λ = 0,5 мин).
"""

import math
from statistics import fmean

from random_numbers import Function, inverse_transform

LAMBDA = 2

if __name__ == '__main__':
    def inverse(z):
        return -math.log(1 - z) / LAMBDA

    intervals = inverse_transform(inverse, 10)
    print('Интервалы, мин:', ', '.join(f'{x:.3f}' for x in intervals))

    sample = inverse_transform(inverse, 10_000)
    print(f'Среднее по 10 000 значениям: {fmean(sample):.4f} (теория {1 / LAMBDA})')

    # То же самое, но формулой из строки, как в интерактивном меню
    same = Function('-ln(1 - z) / 2', 'z')
    print(f'Среднее для формулы «{same}»: {fmean(inverse_transform(same, 10_000)):.4f}')
