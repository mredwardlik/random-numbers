from random import random


def _LimitTheorem(m, d, n):
    sequence = []
    for _ in range(n):
        s = 0
        for _ in range(12):
            s = s + random()
        sequence.append(m + d * (s - 6))
    return sequence


def LimitTheorem(cli, name):
    pass


if __name__ == '__main__':
    m = 5    # Математическое ожидание
    d = 1    # Дисперсия
    n = 10   # Количесвто случайных велечин
    print(_LimitTheorem(m, d, n))