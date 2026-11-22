"""Задача 1. Полная группа событий.

Известно число машин, приезжающих на автомойку в течение последних 150 часов:

    Машин в час | 4  | 5  | 6  | 7
    Частота     | 40 | 60 | 30 | 20

Смоделируйте, сколько машин приедет за 20 часов.
"""

from random_numbers import group_events, to_probabilities

CARS = [4, 5, 6, 7]
FREQUENCIES = [40, 60, 30, 20]
HOURS = 20

if __name__ == '__main__':
    p = to_probabilities(FREQUENCIES)
    result = group_events(p, HOURS, names=[str(cars) for cars in CARS])

    print(f'{"машин в час":>12} {"вероятность":>12} {"часов":>6}')
    for cars, probability in zip(CARS, p):
        print(f'{cars:>12} {probability:>12.4f} {result.counts[str(cars)]:>6}')

    total = sum(cars * result.counts[str(cars)] for cars in CARS)
    expected = HOURS * sum(cars * probability for cars, probability in zip(CARS, p))
    print(f'\nЗа {HOURS} часов приехало {total} машин (в среднем ожидается {expected:.1f}).')
