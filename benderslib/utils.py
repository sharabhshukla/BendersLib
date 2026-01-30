# coding:utf-8

import os
import yaml
import functools

from benderslib import BendersResult

import matplotlib.pyplot as plt


def numerical_cleanup(tol: float = 1e-9):
    """A decorator to clean up numerical noise from the return value of a function.

    This decorator inspects the decorated function's return value and sets any
    floating-point numbers with an absolute value smaller than the tolerance `tol`
    to exactly `0.0`. This is useful for handling numerical inaccuracies that can
    arise from optimization solvers, where coefficients that should be zero appear
    as very small numbers (e.g., 1e-12).

    The cleanup is applied recursively to lists, tuples, and dictionary values.

    Parameters
    ---------------
    tol : float
        The tolerance used to identify and zero out small numbers.
        Defaults to 1e-9.

    Returns
    ---------------
    A wrapper function that cleans its result before returning it.

    Example
    ---------------
    .. code-block:: python

        @numerical_cleanup(tol=1e-8)
        def get_dual_values() -> list[float]:
            # Returns a list like [1.0, 1e-9, -5.0]
            ...
        # The decorated function will return [1.0, 0.0, -5.0]
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            def clean(value):
                if isinstance(value, float):
                    if 0.0 < abs(value) < tol:
                        print('Cleaning value:', value)
                    return 0.0 if abs(value) < tol else value
                elif isinstance(value, list):
                    return [clean(v) for v in value]
                elif isinstance(value, tuple):
                    return tuple(clean(v) for v in value)
                elif isinstance(value, dict):
                    return {k: clean(v) for k, v in value.items()}
                else:
                    return value

            return clean(result)

        return wrapper

    return decorator


def draw_curve(result: BendersResult):
    # Draw convergence curve
    fig, ax1 = plt.subplots()

    ax1.plot(result.lb_list, label='LB')
    ax1.plot(result.ub_list, label='UB')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Objective')
    ax1.set_title('Benders Decomposition')
    ax1.grid(True)

    # Draw Gap on the right axis
    ax2 = ax1.twinx()
    gap = [
        (ub - lb) / abs(ub) if abs(ub) > 1e-4 else float('inf') for lb, ub in zip(result.lb_list, result.ub_list)
    ]
    ax2.plot(gap, 'k--', label='Gap')
    ax2.set_ylabel('Gap (%)')
    ax2.tick_params(axis='y')

    ax2.set_ylim(0, 1)

    # To show the legend for the second axis
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='best')

    plt.show()


def load_config(section: str = None, file='config.yaml') -> dict:
    def convert_strings(data):
        if isinstance(data, dict):
            return {k: convert_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [convert_strings(v) for v in data]
        elif isinstance(data, str):
            if data == "True":
                return True
            elif data == "False":
                return False
            elif data == "None":
                return None
        return data

    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, file)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    config = convert_strings(config)

    if section:
        return config.get(section, {}) or {}
    return config


if __name__ == '__main__':
    pass
