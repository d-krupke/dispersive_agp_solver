"""
This class implements a dispersive AGP solver based on the CP-SAT solver from Google OR-Tools.
It is not competitive with the SAT-based solver, despite CP-SAT using a SAT-solver internally.
Using a SAT-solver directly, allows for a more efficient search strategy.
"""

import itertools
import logging
import math
import typing
from enum import Enum
from typing import Any

from ortools.sat.python import cp_model

from disp_agp_solver._utils.timer import Timer
from disp_agp_solver.instance import Instance

from .._common import GuardCoverage, GuardDistances, WitnessStrategy


class _VarMap:
    """
    I like to create a dedicated container for the variables.
    This comes in handy when building more complex models.
    """

    def __init__(self, n: int, model: cp_model.CpModel, max_dist: int) -> None:
        self._model = model
        self._vars = [self._model.NewBoolVar(f"x_{i}") for i in range(n)]
        self._combi_vars = {
            (g, g_): self._model.NewBoolVar(f"y_{g}_{g_}")
            for g in range(n)
            for g_ in range(g + 1, n)
        }
        self._l = self._model.NewIntVar(0, max_dist, "l")
        for (g, g_), x in self._combi_vars.items():
            self._model.AddBoolOr([self._vars[g].Not(), self._vars[g_].Not(), x])

    def x(self, g: int) -> cp_model.IntVar:
        return self._vars[g]

    def y(self, g: int, g_: int) -> cp_model.IntVar:
        g, g_ = min(g, g_), max(g, g_)
        return self._combi_vars[(g, g_)]

    def l(self) -> cp_model.IntVar:  # noqa: E743
        return self._l

    def get_guards(
        self, get_val: typing.Callable[[cp_model.IntVar], int]
    ) -> typing.List[int]:
        return [g for g, x in enumerate(self._vars) if get_val(x)]


class _CpSatModel:
    """
    As we may have to do multiple solves, we create a dedicated class for the model.
    Bugs in the mathematical model can be hard to detect, thus, the code needs to be
    as simple as possible.
    """

    def __init__(
        self,
        instance: Instance,
        dists: GuardDistances,
        logger: logging.Logger,
        scaling_factor: int = 10_000,
    ) -> None:
        self.logger = logger
        self.instance = instance
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.log_callback = self.logger.info
        self.scaling_factor = scaling_factor
        self._vars = _VarMap(
            instance.num_positions(),
            self.model,
            round(dists.max() * scaling_factor + 1),
        )
        self._dists = dists
        self._build_objective()
        self.upper_bound = math.inf
        self.solution = list(range(instance.num_positions()))
        self.objective = 0
        self._stats = {
            "num_cpsat_solves": 0,
            "num_witnesses": 0,
            "solve_stats": [],
        }

    def _build_objective(self):
        self.model.Maximize(self._vars.l())

        def dist(g: int, g_: int) -> float:
            return round(self._dists.distance(g, g_) * self.scaling_factor)

        for g, g_ in itertools.combinations(range(self.instance.num_positions()), 2):
            self.model.Add(self._vars.l() <= dist(g, g_)).OnlyEnforceIf(
                self._vars.y(g, g_)
            )

    def add_witness(self, guards: typing.List[int]):
        self._stats["num_witnesses"] += 1
        self.model.AddBoolOr([self._vars.x(g) for g in guards])

    def add_upper_bound(self, d: float):
        self.model.Add(self._vars.l() <= round(d * self.scaling_factor))

    def _update_solution(self, status, solver: cp_model.CpSolver):
        self.upper_bound = min(
            self.upper_bound, solver.ObjectiveValue() / self.scaling_factor
        )
        if status != cp_model.UNKNOWN:
            assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
            self.solution = self._vars.get_guards(lambda x: solver.Value(x))
            if len(self.solution) == 1:
                self.objective = math.inf
            else:
                self.objective = solver.ObjectiveValue() / self.scaling_factor
        else:
            self.solution = list(range(self.instance.num_positions()))
            self.objective = 0
        self._stats["solve_stats"].append(
            {
                "CP-SAT": solver.ResponseStats(),
                "upper_bound": self.upper_bound,
                "objective": self.objective,
                "num_witnesses": self._stats["num_witnesses"],
            }
        )

    def solve(
        self, timer: Timer, opt_tol: float
    ) -> typing.Tuple[float, typing.List[int]]:
        self._stats["num_cpsat_solves"] += 1
        solver = self.solver
        solver.parameters.max_time_in_seconds = timer.remaining()
        solver.parameters.relative_gap_limit = opt_tol
        status = solver.Solve(self.model)
        self._update_solution(status, solver)
        return self.objective, self.solution

    def get_stats(self) -> dict[str, Any]:
        return self._stats.copy()


class CpSatOptimizer:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(
        self, instance: Instance, logger: typing.Optional[logging.Logger] = None
    ):
        self._logger = (
            logger if logger is not None else logging.getLogger("CpSatOptimizer")
        )
        self._logger.info("Initializing CP-SAT optimizer")
        self.instance = instance
        self._guard_coverage = GuardCoverage(instance)
        self._dists = GuardDistances(instance, self._guard_coverage)
        self._witness_strategy = WitnessStrategy(
            instance, self._guard_coverage
        )
        self._model = _CpSatModel(instance, self._dists, logger=self._logger)
        self.solution = None
        self.upper_bound = math.inf
        self.objective = 0
        self._logger.info("CP-SAT optimizer initialized")

    def get_opt_gap(self) -> float:
        """
        Return the optimality gap, similar to the one defined by CP-SAT
        """
        return (self.upper_bound - self.objective) / self.objective

    def solve(self, time_limit: float, opt_tol: float = 0.0001):
        try:
            timer = Timer(time_limit)
            for _, guards in self._witness_strategy.get_initial_witnesses():
                self._model.add_witness(guards)
            obj, solution = self._model.solve(timer, opt_tol)
            self.upper_bound = obj
            new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(solution)
            while new_witnesses:
                timer.check()
                for _, guards in new_witnesses:
                    self._model.add_witness(guards)
                self._logger.info("Added %d witnesses.", len(new_witnesses))
                self._model.add_upper_bound(self.upper_bound)
                obj, solution = self._model.solve(timer, opt_tol)
                self.upper_bound = obj
                new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(
                    solution
                )
            self.solution = solution
            if len(self.solution) == 1:
                self.objective = math.inf
            self.objective = obj
            return self.Status.OPTIMAL
        except TimeoutError:
            if self.solution is not None:
                return self.Status.FEASIBLE
        return self.Status.UNKNOWN

    def get_stats(self) -> dict[str, Any]:
        stats = self._model.get_stats()
        stats.update(self._witness_strategy.get_stats())
        return stats
