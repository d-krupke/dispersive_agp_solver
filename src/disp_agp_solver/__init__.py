"""
This package provides an exact solver for the dispersion AGP problem.
The dispersive AGP is a variant of the Art Gallery Problem (AGP) where
the objective is to maximize the dispersion of the selected guards.
The dispersion is the minimum distance between any two guards.
The number of guards does not matter.

The solver is based on a SAT model that is solved using the pysat package.
It iteratively adds distance constraints to the model until the solution
is optimal (detected by infeasibility of the next larger distance).
To ensure total coverage, the solver adds witnesses to the model if needed.
This is similar to the classical AGP solver.

Note that the restriction to vertex guards makes this problem much
more tractable than general point guards.

Dominik Krupke, 2023, Braunschweig

"""

from .instance import Instance
from .optimizer import SatBasedOptimizer
from .plotting import Plotter
from .params import OptimizerParams, SearchStrategy
from .cpsat import CpSatOptimizer
from .gurobi import GurobiSolver

__all__ = ["Instance", "DispAgpSolver", "DispAgpSolverObserver", "SatBasedOptimizer", "Plotter", "OptimizerParams", "SearchStrategy", "CpSatOptimizer", "GurobiSolver"]
