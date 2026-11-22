"""The interactive menu: every method asks its parameters, runs and shows the result."""

from __future__ import annotations

import math
import random
from typing import Callable, NamedTuple, Sequence

from rich import box
from rich.table import Table

from . import distributions as dist
from . import events
from .generators import Davis, Generator, Golenko, LinearCongruential, MiddleSquare, Period
from .stats import frequencies
from .ui import Ui, fmt, formula, integer, probability, real, reals, split_numbers


class Method(NamedTuple):
    section: str
    title: str
    run: Callable[[Ui, random.Random], None]


# ---------------------------------------------------------------- uniform generators

def _period_note(ui: Ui, period: Period | None, limit_text: str) -> None:
    if period is None:
        ui.note(f'Период: [bold]больше {limit_text}[/bold] чисел.')
        return
    repeated = f'числа №{period.start}' if period.start else 'начального значения'
    ui.note(f'Период T = [bold]{period.length}[/bold], отрезок апериодичности L = [bold]{period.aperiodic}[/bold] '
            f'[dim](число №{period.aperiodic} — повтор {repeated})[/dim]')


def _show_uniform(ui: Ui, generator: Generator, n: int, integers: str | None = None,
                  period_limit: int = 200_000) -> None:
    period = generator.period(period_limit)
    values, extra = [], []
    for _ in range(n):
        values.append(next(generator))
        if integers:
            extra.append(generator.z)
    ui.sequence(values, 'r', (integers, extra) if integers else None)
    _period_note(ui, period, f'{period_limit:,}'.replace(',', ' '))
    if period is not None and period.length == 1 and generator.value == 0:
        ui.note('[yellow]Последовательность выродилась в ноль: выберите другое начальное значение.[/yellow]')
    if n >= 2:
        ui.print()
        ui.summary(values, 0.5, 1 / 12)
    if n >= 20:
        ui.histogram(values, 10, 0, 1)


def middle_square(ui: Ui, rng: random.Random) -> None:
    ui.title('Метод середины квадрата', 'zᵢ₊₁ = средние k цифр числа zᵢ²,  rᵢ = zᵢ / 10ᵏ')

    def seed(text: str) -> str:
        MiddleSquare(text)
        return text.strip().replace(',', '.')

    z0 = ui.ask('Начальное значение z₀ (0.8933 или 5735)', seed, '0.8933')
    n = ui.ask('Сколько чисел n', integer(1, 100_000), 10)
    generator = MiddleSquare(z0)
    ui.note(f'[dim]Разрядность k = {generator.digits}[/dim]\n')
    _show_uniform(ui, generator, n)


def linear_congruential(ui: Ui, rng: random.Random) -> None:
    ui.title('Линейный конгруэнтный метод', 'zᵢ₊₁ = (a·zᵢ + c) mod m,  rᵢ = zᵢ / m')
    m = ui.ask('Модуль m', integer(2), 100)
    a = ui.ask('Множитель a', integer(1, m - 1), 21 if m > 21 else 1)
    c = ui.ask('Приращение c', integer(0, m - 1), 17 if m > 17 else 0)
    z0 = ui.ask('Начальное значение z₀', integer(0, m - 1), 7 if m > 7 else 0)
    n = ui.ask('Сколько чисел n', integer(1, 100_000), 10)
    ui.print()
    _show_uniform(ui, LinearCongruential(z0, a=a, c=c, m=m), n, integers='zᵢ')


def davis(ui: Ui, rng: random.Random) -> None:
    ui.title('Метод Дэвиса (аддитивный)', 'zᵢ = (zᵢ₋₁ + zᵢ₋ₖ) mod m,  rᵢ = zᵢ / m,  k — число начальных значений')

    def seeds(text: str) -> list[str]:
        values = split_numbers(text)
        reals(2, 0)(text)
        return [value.replace(',', '.') for value in values]

    m = ui.ask('Модуль m', real(above=0), 1)
    while True:
        z = ui.ask('Начальные значения через пробел', seeds, '0.36 0.45 0.62')
        try:
            generator = Davis(z, m)
            break
        except ValueError as error:
            ui.error(str(error))
    n = ui.ask('Сколько чисел n', integer(1, 100_000), 10)
    ui.print()
    _show_uniform(ui, generator, n)


def golenko(ui: Ui, rng: random.Random) -> None:
    ui.title('Метод возмущений Голенко',
             'линейный конгруэнтный метод, каждое p-е число — середина квадрата предыдущего')
    m = ui.ask('Модуль m', integer(2), 42782)
    a = ui.ask('Множитель a', integer(1, m - 1), 302 if m > 302 else 1)
    c = ui.ask('Приращение c', integer(0, m - 1), 4965 if m > 4965 else 0)
    z0 = ui.ask('Начальное значение z₀', integer(0, m - 1), 120 if m > 120 else 0)
    p = ui.ask('Период возмущений p', integer(2), 5)
    k = ui.ask('Разрядов в возмущении k', integer(2, 12), 4)
    n = ui.ask('Сколько чисел n', integer(1, 100_000), 10)
    ui.print()
    _show_uniform(ui, Golenko(z0, a=a, c=c, m=m, period=p, digits=k), n, period_limit=50_000)


# ---------------------------------------------------------------- events

TWO_EVENTS = {'AB': 'A и B', 'A!B': 'только A', '!AB': 'только B', '!A!B': 'ни A, ни B'}


def _show_experiment(ui: Ui, result: events.Experiment, descriptions: dict[str, str]) -> None:
    ui.print()
    ui.experiment(((outcome, descriptions.get(outcome, ''), result.probabilities[outcome],
                    result.counts[outcome]) for outcome in result.outcomes), result.n)


def simple_events(ui: Ui, rng: random.Random) -> None:
    ui.title('Простые события', 'событие A происходит, если z < p')
    p = ui.ask('Вероятность события p', probability, 0.2)
    n = ui.ask('Количество испытаний n', integer(1, 10_000_000), 200)
    result = events.simple_events(p, n, rng)
    _show_experiment(ui, result, {'A': 'произошло', '!A': 'не произошло'})


def complex_events(ui: Ui, rng: random.Random) -> None:
    ui.title('Сложные события (независимые)', 'A: z₁ < p₁,  B: z₂ < p₂')
    p1 = ui.ask('Вероятность A  p₁', probability, 0.15)
    p2 = ui.ask('Вероятность B  p₂', probability, 0.2)
    n = ui.ask('Количество испытаний n', integer(1, 10_000_000), 1000)
    _show_experiment(ui, events.complex_events(p1, p2, n, rng), TWO_EVENTS)


def conditional_events(ui: Ui, rng: random.Random) -> None:
    ui.title('Условная вероятность (зависимые события)',
             'A: z₁ < P(A),  B: z₂ < P(B|A), если A произошло, иначе z₂ < P(B|!A)')
    pa = ui.ask('Вероятность A  P(A)', probability, 0.6)
    pb_a = ui.ask('Вероятность B, если A произошло  P(B|A)', probability, 0.5)
    pb_not_a = ui.ask('Вероятность B, если A не произошло  P(B|!A)', probability, 0.75)
    n = ui.ask('Количество испытаний n', integer(1, 10_000_000), 10000)
    result = events.conditional_events(pa, pb_a, pb_not_a, n, rng)
    _show_experiment(ui, result, TWO_EVENTS)
    pb = pa * pb_a + (1 - pa) * pb_not_a
    seen = result.frequency('AB') + result.frequency('!AB')
    ui.note(f'Полная вероятность P(B) = {fmt(pb)}, частота B = {fmt(seen)}')


def group_events(ui: Ui, rng: random.Random) -> None:
    ui.title('Полная группа событий', 'событие i происходит, если z попало в i-й отрезок длины pᵢ')
    values = ui.ask('Вероятности (или частоты) событий через пробел', reals(2, 0), '0.1 0.2 0.3 0.4')
    total = math.fsum(values)
    if abs(total - 1) > events.PROBABILITY_TOLERANCE:
        values = events.to_probabilities(values)
        ui.note(f'[yellow]Сумма равна {fmt(total)}, а не 1: значения приняты за частоты '
                f'и пронормированы.[/yellow]')
    n = ui.ask('Количество испытаний n', integer(1, 10_000_000), 1000)
    _show_experiment(ui, events.group_events(values, n, rng), {})


# ---------------------------------------------------------------- distributions

def _show_discrete(ui: Ui, ks: Sequence[int], probabilities: Sequence[float], tail: float,
                   tail_label: str, sample: Sequence[int]) -> None:
    counts = frequencies(sample)
    last = ks[-1]
    rows = [(str(k), p, counts.get(k, 0)) for k, p in zip(ks, probabilities)]
    rows.append((tail_label, tail, sum(c for k, c in counts.items() if k > last)))
    top = max(max(p for _, p, _ in rows), max(c for _, _, c in rows) / len(sample)) or 1
    table = ui.table('k', 'P(X = k)', 'частота', '')
    table.columns[-1].justify = 'left'
    for label, p, count in rows:
        if label == tail_label and p < 5e-7 and count == 0:
            continue
        table.add_row(label, fmt(p), fmt(count / len(sample)), ui.bar(count / len(sample) / top, 24))
    table.caption = f'частоты по выборке из {len(sample)} значений'
    ui.print()
    ui.print(table)


def geometric(ui: Ui, rng: random.Random) -> None:
    ui.title('Геометрическое распределение', 'P(X = k) = (1 − p)ᵏ⁻¹ · p,  X = ⌊ln z / ln(1 − p)⌋ + 1')
    p = ui.ask('Вероятность успеха p', real(maximum=1, above=0), 0.23)
    rows = ui.ask('Сколько значений k показать', integer(1, 200), 10)
    size = ui.ask('Размер выборки N', integer(1, 1_000_000), 1000)
    sample = dist.geometric_sample(p, size, rng)
    _show_discrete(ui, range(1, rows + 1), dist.geometric_probabilities(p, rows),
                   (1 - p) ** rows, f'> {rows}', sample)
    ui.summary(sample, 1 / p, (1 - p) / p ** 2)


def poisson(ui: Ui, rng: random.Random) -> None:
    ui.title('Распределение Пуассона', 'P(X = k) = λᵏ · e^(−λ) / k!,  λ = n · p')
    n = ui.ask('Количество испытаний n', integer(1, 10_000_000), 100)
    p = ui.ask('Вероятность события в испытании p', real(maximum=1, above=0), 0.08)
    lam = n * p
    ui.note(f'[dim]λ = n · p = {fmt(lam)}[/dim]')
    size = ui.ask('Размер выборки N', integer(1, 100_000), 1000)
    probabilities, cumulative, k = [], 0.0, 0
    while True:
        probabilities.append(dist.poisson_probability(lam, k))
        cumulative += probabilities[-1]
        if (k >= lam and 1 - cumulative < 5e-4) or k >= n or len(probabilities) >= 60:
            break
        k += 1
    sample = dist.poisson_sample(lam, size, rng)
    _show_discrete(ui, range(len(probabilities)), probabilities, max(0.0, 1 - cumulative),
                   f'> {len(probabilities) - 1}', sample)
    ui.summary(sample, lam, lam)


def poisson_process(ui: Ui, rng: random.Random) -> None:
    ui.title('Простейший поток событий', 'tᵢ = tᵢ₋₁ − ln z / λ,  интервалы распределены экспоненциально')
    lam = ui.ask('Интенсивность потока λ (событий в единицу времени)', real(above=0), '8/24')
    t = ui.ask('Время моделирования t', real(above=0), 100)
    times = dist.poisson_process(lam, t, rng)
    ui.print()
    if not times:
        ui.note(f'За время {fmt(t)} не произошло ни одного события (в среднем ожидается {fmt(lam * t)}).')
        return
    intervals = [b - a for a, b in zip([0.0] + times, times)]
    ui.sequence(times, 't', ('Δt', intervals))
    ui.note(f'Событий: [bold]{len(times)}[/bold], в среднем ожидается λ·t = {fmt(lam * t)}')
    ui.print()
    ui.print('  [bold]Интервалы между событиями[/bold]')
    ui.summary(intervals, 1 / lam, 1 / lam ** 2)


def normal(ui: Ui, rng: random.Random) -> None:
    ui.title('Нормальное распределение (центральная предельная теорема)',
             'x = m + σ · (z₁ + z₂ + … + z₁₂ − 6)')
    m = ui.ask('Математическое ожидание m', real(), 5)
    sigma = ui.ask('Среднеквадратическое отклонение σ', real(minimum=0), 1)
    n = ui.ask('Сколько значений n', integer(1, 1_000_000), 1000)
    sample = dist.normal_clt(m, sigma, n, rng)
    _show_continuous(ui, sample, m, sigma ** 2)


def _show_continuous(ui: Ui, sample: Sequence[float], mean: float | None = None,
                     variance: float | None = None) -> None:
    ui.print()
    first = ', '.join(fmt(x) for x in sample[:6])
    ui.note(f'[dim]Первые значения:[/dim] {first}{", …" if len(sample) > 6 else ""}\n')
    ui.summary(sample, mean, variance)
    if len(sample) >= 20:
        ui.histogram(sample, 12)


def inverse_function(ui: Ui, rng: random.Random) -> None:
    ui.title('Метод обратной функции', 'x = F⁻¹(z): z равномерно на (0, 1), F — функция распределения')
    ui.note('[dim]Например: экспоненциальное -ln(1 - z) / λ, равномерное a + (b - a)*z, '
            'Вейбулла (-ln(1 - z))^(1/k)[/dim]')
    inverse = ui.ask('Обратная функция F⁻¹(z)', formula('z'), '-ln(1 - z) / 2')
    n = ui.ask('Сколько значений n', integer(1, 1_000_000), 1000)
    _show_continuous(ui, dist.inverse_transform(inverse, n, rng))


def neumann(ui: Ui, rng: random.Random) -> None:
    ui.title('Метод исключения Неймана',
             'точка (a + z₁(b − a), M·z₂) принимается, если лежит под кривой y = f(x)')
    density = ui.ask('Плотность f(x), можно ненормированную', formula('x'), '2*x + x^4')
    a = ui.ask('Левая граница a', real(), 1)
    b = ui.ask('Правая граница b', real(above=a), 5)

    def height(text: str) -> float | None:
        return None if text.lower() in ('авто', 'auto') else real(above=0)(text)

    m = ui.ask('Высота прямоугольника M', height, 'авто')
    n = ui.ask('Сколько значений n', integer(1, 1_000_000), 1000)
    result = dist.neumann(density, a, b, n, rng, m)
    ui.print()
    ui.note(f'M = {fmt(result.height)}, брошено точек: {result.attempts}, '
            f'принято: {len(result.x)} ({100 * result.acceptance:.1f} %)')
    _show_continuous(ui, result.x, *dist.density_moments(density, a, b))


METHODS = [
    Method('Датчики равномерных чисел', 'Метод середины квадрата', middle_square),
    Method('Датчики равномерных чисел', 'Линейный конгруэнтный метод', linear_congruential),
    Method('Датчики равномерных чисел', 'Метод Дэвиса', davis),
    Method('Датчики равномерных чисел', 'Метод возмущений Голенко', golenko),
    Method('Моделирование событий', 'Простые события', simple_events),
    Method('Моделирование событий', 'Сложные события', complex_events),
    Method('Моделирование событий', 'Условная вероятность', conditional_events),
    Method('Моделирование событий', 'Полная группа событий', group_events),
    Method('Случайные величины', 'Геометрическое распределение', geometric),
    Method('Случайные величины', 'Распределение Пуассона', poisson),
    Method('Случайные величины', 'Простейший поток событий', poisson_process),
    Method('Случайные величины', 'Нормальное распределение (ЦПТ)', normal),
    Method('Случайные величины', 'Метод обратной функции', inverse_function),
    Method('Случайные величины', 'Метод исключения Неймана', neumann),
]


def show_menu(ui: Ui) -> None:
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1), border_style='dim')
    table.add_column(justify='right', style='bold magenta')
    table.add_column()
    section = None
    for number, method in enumerate(METHODS, 1):
        if method.section != section:
            if section is not None:
                table.add_section()
            section = method.section
            table.add_row('', f'[bold cyan]{section}[/bold cyan]')
        table.add_row(str(number), method.title)
    table.add_section()
    table.add_row('0', '[dim]Выход[/dim]')
    ui.print()
    ui.print(table)


def run(ui: Ui, rng: random.Random) -> None:
    """Show the menu until the user chooses 0, Ctrl+C or the input ends."""
    while True:
        show_menu(ui)
        try:
            choice = ui.ask('Номер метода', integer(0, len(METHODS)))
        except (EOFError, KeyboardInterrupt):
            ui.print()
            return
        if choice == 0:
            return
        try:
            METHODS[choice - 1].run(ui, rng)
        except ValueError as error:
            ui.error(str(error))
        except KeyboardInterrupt:
            ui.print('\n  [dim]Прервано.[/dim]')
        except EOFError:
            ui.print()
            return
        try:
            ui.pause()
        except (EOFError, KeyboardInterrupt):
            ui.print()
            return
