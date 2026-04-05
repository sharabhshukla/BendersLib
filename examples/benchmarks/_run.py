# coding:utf-8

"""
_run
=======================================================

Run all the benchmarks.
"""

import os
import sys

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:
    sys.path.insert(0, os.path.abspath("."))

from linear import run as run1
from integer import run as run2
from lbbd_location import run as run3
from _utils import draw

# %%
# Solve the benchmark problems using BendersLib.

# run1(solve_methods=['bd'], dry_run=False)
# run2(solve_methods=['bd'], dry_run=False)
# run3(solve_methods=['bd'], dry_run=False)

# %%
# Solve the benchmark problems using the monolithic model.

# run1(solve_methods=['de'], dry_run=False)
# run2(solve_methods=['de'], dry_run=False)
# run3(solve_methods=['de'], dry_run=False)

# %%
# Collect the data and draw the results.

# data1 = run1(dry_run=True)
# data2 = run2(dry_run=True)
# data3 = run3(dry_run=True)
# draw(
#     [data1, data2, data3],
#     ['Linear Subproblems', 'Integer Subproblems', 'Custom Solver and Cut']
# )
