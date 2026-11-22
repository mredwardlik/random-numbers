"""Random numbers, events and random variables for a simulation course.

Uniform generators (:mod:`random_numbers.generators`), simulation of events
(:mod:`random_numbers.events`), distributions and sampling methods
(:mod:`random_numbers.distributions`) and an interactive menu
(``random-numbers`` command).
"""

from .distributions import (Rejection, geometric_probabilities, geometric_sample, inverse_transform,
                            neumann, normal_clt, poisson_probabilities, poisson_probability,
                            poisson_process, poisson_sample)
from .events import (Experiment, complex_events, conditional_events, group_events, simple_events,
                     to_probabilities)
from .expression import Function
from .generators import (Davis, Golenko, LinearCongruential, MiddleSquare, Period, davis, golenko,
                         lcg, middle_square)

__version__ = '2.0.0'

__all__ = [
    'Davis', 'Experiment', 'Function', 'Golenko', 'LinearCongruential', 'MiddleSquare', 'Period',
    'Rejection', 'complex_events', 'conditional_events', 'davis', 'geometric_probabilities',
    'geometric_sample', 'golenko', 'group_events', 'inverse_transform', 'lcg', 'middle_square',
    'neumann', 'normal_clt', 'poisson_probabilities', 'poisson_probability', 'poisson_process',
    'poisson_sample', 'simple_events', 'to_probabilities',
]
