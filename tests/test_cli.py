import io

import pytest
from rich.console import Console

from random_numbers import __version__
from random_numbers.cli import main
from random_numbers.menu import METHODS
from random_numbers.ui import Ui


def run(*lines, seed=1):
    output = io.StringIO()
    ui = Ui(Console(file=output, width=120, color_system=None), lines)
    assert main(['--seed', str(seed)], ui) == 0
    return output.getvalue()


@pytest.mark.parametrize('number', range(1, len(METHODS) + 1))
def test_every_method_runs_with_defaults(number):
    # empty answers take the defaults; 30 empty lines are more than any method asks
    text = run(str(number), *[''] * 30)
    assert 'Enter — вернуться в меню' in text
    text = text.split('Enter — вернуться в меню')[0]
    assert METHODS[number - 1].title.split(' (')[0] in text
    assert '✗' not in text
    assert 'Traceback' not in text


def test_exit_with_zero():
    text = run('0')
    assert 'Номер метода' in text


def test_end_of_input_exits():
    assert 'Номер метода' in run()


def test_invalid_answers_are_asked_again():
    text = run('99', 'abc', '5', '2', '0.5', '-3', '100', '', '0')
    assert 'Значение должно быть не больше 14' in text
    assert 'Нужно целое число, а не «abc»' in text
    assert 'Вероятность должна быть в диапазоне [0, 1]' in text
    assert 'Значение должно быть не меньше 1' in text
    assert '100 испытаний' in text


def test_library_error_returns_to_menu():
    text = run('14', 'x - 3', '0', '1', '', '', '', '0')
    assert 'отрицательна' in text
    assert text.count('Номер метода') == 2


def test_same_seed_same_result():
    assert run('12', '', '', '', '', seed=5) == run('12', '', '', '', '', seed=5)
    assert run('12', '', '', '', '', seed=5) != run('12', '', '', '', '', seed=6)


def test_lcg_output():
    text = run('2', '', '', '', '', '3', '')
    assert '│ 1 │ 64 │ 0.64 │' in text
    assert 'Период T = 100' in text


def test_group_frequencies_are_normalized():
    text = run('8', '40 60 30 20', '20', '')
    assert 'пронормированы' in text
    assert '0.266667' in text


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(['--version'])
    assert __version__ in capsys.readouterr().out
