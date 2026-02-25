# coding:utf-8

import os
import yaml
import math

from benderslib import BendersResult

import matplotlib.pyplot as plt


def draw_curve(result: BendersResult):
    # Draw convergence curve
    fig, ax1 = plt.subplots()

    ax1.plot(result.lb_list, label='Lower Bound')
    ax1.plot(result.ub_list, label='Upper Bound')
    ax1.plot(result.obj_list, label='Incumbent')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Objective')
    ax1.set_title('Benders Decomposition')
    ax1.grid(True)

    # Draw Gap on the right axis
    ax2 = ax1.twinx()
    gap = [
        (obj - lb) / abs(obj) if abs(obj) > 1e-4 else float('inf')
        for lb, obj in zip(result.lb_list, result.obj_list)
    ]
    ax2.plot(gap, 'k--', label='Gap')
    ax2.set_ylabel('Gap')
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


def is_all_integer(vals, tol=1e-5):
    for v in vals:
        if abs(v - round(v)) > tol:
            return False
    return True


def normalize_cut(cut, max_norm: float = 1e5):
    """
    Normalize a Benders cut if its L2 norm exceeds a threshold.

    This function scales down the cut's coefficients and right-hand side
    if the L2 norm of the coefficient vector is greater than `max_norm`.
    This can help improve numerical stability in the master problem solver.

    Parameters
    ----------

    cut : Cut
        The Benders cut to normalize.
    max_norm : float, optional
        The maximum allowed L2 norm for the cut's coefficients.
        Defaults to 1e5.
    """
    # Extract coefficients
    a = cut.coefs

    # Calculate L2 norm
    norm = math.sqrt(sum(c * c for c in a))

    if norm > max_norm:
        scale = max_norm / norm

        # Modify the cut
        cut.coefs = [c * scale for c in cut.coefs]
        cut.rhs *= scale

    return cut
