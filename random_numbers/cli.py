"""Command line entry point: ``random-numbers [--seed N]`` opens the interactive menu."""

from __future__ import annotations

import argparse
import random
import sys
from typing import Sequence

from . import __version__
from .menu import run
from .ui import Ui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='random-numbers',
        description='Моделирование случайных чисел, событий и величин: интерактивное меню.',
    )
    parser.add_argument('-s', '--seed', type=int, metavar='N',
                        help='зерно генератора: одинаковое зерно даёт одинаковые результаты')
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    return parser


def use_utf8() -> None:
    """Formulas use symbols like zᵢ₊₁ that cp1251 and cp866 lack: a redirected
    output on Windows would fail on them. Consoles are already UTF-8."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        encoding = (getattr(stream, 'encoding', None) or '').lower().replace('-', '')
        if encoding != 'utf8' and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')


def main(argv: Sequence[str] | None = None, ui: Ui | None = None) -> int:
    args = build_parser().parse_args(argv)
    if ui is None:
        use_utf8()
        ui = Ui()
    ui.print(f'[bold magenta]random-numbers[/bold magenta] [dim]{__version__}[/dim] · '
             'моделирование случайных чисел, событий и величин')
    if args.seed is not None:
        ui.print(f'[dim]Зерно генератора: {args.seed}[/dim]')
    run(ui, random.Random(args.seed))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
