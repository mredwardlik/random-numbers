"""Console input with validation and the tables, histograms and summaries of the menu."""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Callable, Iterable, Sequence, TypeVar

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from .expression import Function
from .stats import describe, histogram, nice_range

T = TypeVar('T')
Parser = Callable[[str], T]

BAR_WIDTH = 32
ROWS_LIMIT = 25
ACCENT = 'magenta'


def fmt(value: float) -> str:
    """Short form of a number: ``0.7984``, ``12.3457``, ``2.3e-10``.

    >>> fmt(0.7984), fmt(1 / 3), fmt(2.0), fmt(2.3e-10), fmt(123456.78)
    ('0.7984', '0.333333', '2', '2.3e-10', '123457')
    """
    if isinstance(value, int):
        return str(value)
    if value == 0:
        return '0'
    return f'{value:.6g}'


# ---------------------------------------------------------------- parsers

def _number(text: str) -> float:
    """``0.14``, ``0,14``, ``1e-6`` or a fraction ``8/24``."""
    source = text.strip().replace(',', '.').replace(' ', '')
    try:
        if '/' in source:
            top, bottom = source.split('/')
            return float(Fraction(top) / Fraction(bottom))
        number = float(source)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f'«{text.strip()}» — не число.') from None
    if not math.isfinite(number):
        raise ValueError('Нужно конечное число.')
    return number


def _bounds(value: float, minimum: float | None, maximum: float | None,
            above: float | None) -> None:
    if above is not None and value <= above:
        raise ValueError(f'Значение должно быть больше {fmt(above)}.')
    if minimum is not None and value < minimum:
        raise ValueError(f'Значение должно быть не меньше {fmt(minimum)}.')
    if maximum is not None and value > maximum:
        raise ValueError(f'Значение должно быть не больше {fmt(maximum)}.')


def real(minimum: float | None = None, maximum: float | None = None,
         above: float | None = None) -> Parser[float]:
    def parse(text: str) -> float:
        value = _number(text)
        _bounds(value, minimum, maximum, above)
        return value
    return parse


def integer(minimum: int | None = None, maximum: int | None = None) -> Parser[int]:
    def parse(text: str) -> int:
        source = text.strip().replace(' ', '').replace('_', '')
        try:
            value = int(source)
        except ValueError:
            raise ValueError(f'Нужно целое число, а не «{text.strip()}».') from None
        _bounds(value, minimum, maximum, None)
        return value
    return parse


def probability(text: str) -> float:
    value = _number(text)
    if not 0 <= value <= 1:
        raise ValueError('Вероятность должна быть в диапазоне [0, 1].')
    return value


def split_numbers(text: str) -> list[str]:
    """Numbers separated by spaces or semicolons; a comma inside a number is a decimal point.

    >>> split_numbers('0.1, 0.2 0,3;0.4')
    ['0.1', '0.2', '0,3', '0.4']
    """
    tokens = text.replace(';', ' ').split()
    if len(tokens) == 1 and tokens[0].count(',') > 1:
        tokens = tokens[0].split(',')
    return [token.strip(',') for token in tokens if token.strip(',')]


def reals(count: int = 1, minimum: float | None = None) -> Parser[list[float]]:
    def parse(text: str) -> list[float]:
        values = [_number(token) for token in split_numbers(text)]
        if len(values) < count:
            raise ValueError(f'Нужно хотя бы {count} числа через пробел.')
        for value in values:
            _bounds(value, minimum, None, None)
        return values
    return parse


def formula(variable: str) -> Parser[Function]:
    return lambda text: Function(text, variable)


# ---------------------------------------------------------------- console

class Ui:
    """Questions and answers in the console.

    ``lines`` replaces the keyboard (tests and the demo): every line is echoed
    after its prompt as if typed.
    """

    def __init__(self, console: Console | None = None, lines: Iterable[str] | None = None):
        self.console = console or Console(highlight=False)
        self._lines = iter(lines) if lines is not None else None

    # input

    def read(self, prompt: str) -> str:
        if self._lines is None:
            return self.console.input(prompt)
        self.console.print(prompt, end='')
        try:
            line = next(self._lines)
        except StopIteration:
            self.console.print()
            raise EOFError from None
        self.console.print(Text(line, style='bold'))
        return line

    def ask(self, label: str, parse: Parser[T], default: object = None) -> T:
        """Ask until the answer parses. An empty answer takes the default."""
        hint = f' [dim]\\[{escape(str(default))}][/dim]' if default is not None else ''
        while True:
            text = self.read(f'  {label}{hint}: ').strip()
            if not text:
                if default is None:
                    self.error('Введите значение.')
                    continue
                text = str(default)
            try:
                return parse(text)
            except ValueError as error:
                self.error(str(error))

    def pause(self) -> None:
        self.read('\n[dim]Enter — вернуться в меню[/dim] ')

    # output

    def print(self, *args, **kwargs) -> None:
        self.console.print(*args, **kwargs)

    def error(self, text: str) -> None:
        self.console.print(f'  [red]✗[/red] {escape(text)}')

    def title(self, text: str, formula_text: str = '') -> None:
        self.console.print()
        self.console.rule(f'[bold {ACCENT}]{escape(text)}[/bold {ACCENT}]', align='left', style=ACCENT)
        if formula_text:
            self.console.print(f'  [cyan]{escape(formula_text)}[/cyan]')
        self.console.print()

    def note(self, text: str) -> None:
        self.console.print(f'  {text}')

    def table(self, *headers: str, title: str | None = None) -> Table:
        table = Table(*headers, box=box.ROUNDED, header_style=f'bold {ACCENT}', title=title,
                      title_justify='left', title_style='bold', padding=(0, 1))
        for column in table.columns[1:]:
            column.justify = 'right'
        return table

    @staticmethod
    def bar(share: float, width: int = BAR_WIDTH) -> Text:
        cells = max(0.0, min(share, 1.0)) * width
        full = int(cells)
        eighths = int((cells - full) * 8)
        if share > 0 and not full and not eighths:
            eighths = 1  # a nonzero value is always visible
        return Text('█' * full + ('▏▎▍▌▋▊▉'[eighths - 1] if eighths else ''), style='cyan')

    def sequence(self, values: Sequence[float], label: str = 'r',
                 extra: tuple[str, Sequence] | None = None) -> None:
        """Numbered values; long sequences are cut in the middle."""
        headers = ['i']
        if extra:
            headers.append(extra[0])
        headers.append(f'{label}ᵢ')
        table = self.table(*headers)
        indices = list(range(len(values)))
        if len(values) > ROWS_LIMIT:
            head = ROWS_LIMIT - 5
            indices = indices[:head] + [-1] + indices[-4:]
        for i in indices:
            if i == -1:
                table.add_row('…', *([''] * (len(headers) - 1)), style='dim')
                continue
            row = [str(i + 1)]
            if extra:
                row.append(fmt(extra[1][i]))
            row.append(fmt(values[i]))
            table.add_row(*row)
        self.console.print(table)
        if len(values) > ROWS_LIMIT:
            self.note(f'[dim]Показаны первые {ROWS_LIMIT - 5} и последние 4 из {len(values)} чисел.[/dim]')

    def summary(self, values: Sequence[float], mean: float | None = None,
                variance: float | None = None) -> None:
        """Sample mean and variance next to the theoretical ones."""
        stats = describe(values)
        table = self.table('', 'выборка', 'теория')
        table.add_row('среднее M', fmt(stats.mean), fmt(mean) if mean is not None else '—')
        table.add_row('дисперсия D', fmt(stats.variance), fmt(variance) if variance is not None else '—')
        table.add_row('σ = √D', fmt(stats.deviation), fmt(math.sqrt(variance)) if variance is not None else '—')
        table.add_row('min … max', f'{fmt(stats.minimum)} … {fmt(stats.maximum)}', '')
        self.console.print(table)

    def histogram(self, values: Sequence[float], bins: int = 10, low: float | None = None,
                  high: float | None = None) -> None:
        if low is None or high is None:
            low, high, bins = nice_range(min(values), max(values), bins)
        rows = histogram(values, bins, low, high)
        top = max(count for _, _, count in rows) or 1
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column(justify='right', style='dim')
        table.add_column()
        table.add_column(justify='right')
        closing = len(rows) - 1
        for i, (left, right, count) in enumerate(rows):
            span = f'[{fmt(left)}; {fmt(right)}{"]" if i == closing else ")"}'
            table.add_row(span, self.bar(count / top), str(count))
        self.console.print('  [bold]Гистограмма[/bold]')
        self.console.print(table)

    def experiment(self, rows: Iterable[tuple[str, str, float, int]], n: int) -> None:
        """Outcome, description, theoretical probability and count of n trials."""
        table = self.table('исход', 'событие', 'P теор.', 'раз', 'частота', '')
        table.columns[1].justify = 'left'
        table.columns[-1].justify = 'left'
        for outcome, description, p, count in rows:
            frequency = count / n
            table.add_row(f'[bold]{escape(outcome)}[/bold]', description, fmt(p), str(count),
                          fmt(frequency), self.bar(frequency, 20))
        table.caption = f'{n} испытаний'
        self.console.print(table)
