"""Safe math formulas typed by the user, such as ``2*x + x^4`` or ``-ln(1 - z) / 2``.

Only numbers, one variable, arithmetic and functions from :mod:`math` are
allowed: the text is parsed into a syntax tree and evaluated without ``eval``.

>>> f = Function('2*x + x^4')
>>> f(2)
20.0
>>> Function('2^3^2')(0)  # right-associative, like in math
512.0
>>> round(Function('-ln(1 - z) / 2', 'z')(0.5), 4)
0.3466
>>> Function('__import__("os").system("calc")')  # doctest: +ELLIPSIS
Traceback (most recent call last):
...
ValueError: Неизвестная функция «__import__('os').system». Доступны: abs, acos, ...
>>> Function('x + y')
Traceback (most recent call last):
...
ValueError: Неизвестное имя «y». Переменная — x.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Callable

FUNCTIONS: dict[str, Callable[..., float]] = {
    name: getattr(math, name) for name in (
        'sqrt', 'exp', 'log', 'log2', 'log10', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
        'sinh', 'cosh', 'tanh', 'floor', 'ceil', 'erf', 'gamma',
    )
}
FUNCTIONS.update(ln=math.log, abs=abs, min=min, max=max, pow=math.pow)
CONSTANTS = {'pi': math.pi, 'e': math.e, 'tau': math.tau}

_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_LENGTH = 300


class Function:
    """A formula of one variable that can be called like a Python function."""

    def __init__(self, text: str, variable: str = 'x'):
        source = text.strip()
        if not source:
            raise ValueError('Введите формулу.')
        if len(source) > MAX_LENGTH:
            raise ValueError(f'Формула длиннее {MAX_LENGTH} символов.')
        try:
            # x^2 means a power, as in math notation (in Python ^ is xor with a lower priority)
            tree = ast.parse(source.replace('^', '**'), mode='eval')
        except SyntaxError:
            raise ValueError(f'Не удалось разобрать формулу «{source}».') from None
        self.text = source
        self.variable = variable
        self._check(tree.body)
        self._tree = tree.body

    def _check(self, node: ast.AST) -> None:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError('В формуле допустимы только числа.')
        elif isinstance(node, ast.Name):
            if node.id != self.variable and node.id not in CONSTANTS:
                raise ValueError(f'Неизвестное имя «{node.id}». Переменная — {self.variable}.')
        elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            self._check(node.left)
            self._check(node.right)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            self._check(node.operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS or node.keywords:
                name = ast.unparse(node.func)
                raise ValueError(f'Неизвестная функция «{name}». Доступны: {", ".join(sorted(FUNCTIONS))}.')
            for argument in node.args:
                self._check(argument)
        else:
            raise ValueError('В формуле допустимы числа, переменная, + − * / ^ и функции math.')

    def _eval(self, node: ast.AST, value: float) -> float:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return value if node.id == self.variable else CONSTANTS[node.id]
        if isinstance(node, ast.BinOp):
            left, right = self._eval(node.left, value), self._eval(node.right, value)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise OverflowError('слишком большая степень')
            return _BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp):
            return _UNARY[type(node.op)](self._eval(node.operand, value))
        return FUNCTIONS[node.func.id](*(self._eval(argument, value) for argument in node.args))

    def __call__(self, value: float) -> float:
        try:
            result = self._eval(self._tree, value)
            if isinstance(result, complex):
                raise ValueError('получилось комплексное число')
            return float(result)
        except ZeroDivisionError:
            raise ValueError('деление на ноль') from None
        except (OverflowError, ValueError, TypeError) as error:
            raise ValueError(str(error) or 'ошибка вычисления') from None

    def __repr__(self) -> str:
        return f'Function({self.text!r}, {self.variable!r})'

    def __str__(self) -> str:
        return self.text
