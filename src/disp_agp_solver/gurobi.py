"""
This file implements an optimizer for the dispersion AGP problem based on Gurobi.
It is not competitive with the SAT-based solver, and is only included for comparison.
"""

import itertools
import logging
import math
import typing
from enum import Enum

import gurobipy as gp
from gurobipy import GRB

from .guard_coverage import GuardCoverage
from .guard_distances import GuardDistances
from .instance import Instance
from .params import OptimizerParams
from .witness_strategy import WitnessStrategy


class _VarMap:
    def __init__(self, instance: Instance, model: gp.Model) -> None:
        self._vars = [
            model.addVar(vtype=gp.GRB.BINARY, name=f"x_{i}")
            for i in range(instance.num_positions())
        ]
        self._l = model.addVar(vtype=gp.GRB.CONTINUOUS, name="l")

    def x(self, g: int) -> gp.Var:
        return self._vars[g]

    def l(self) -> gp.Var:
        return self._l

    def get_guards(self, get_val: typing.Callable[[gp.Var], int]) -> typing.List[int]:
        return [g for g, x in enumerate(self._vars) if get_val(x)]


class GurobiOptimizer:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(
        self, instance: Instance, logger: typing.Optional[logging.Logger] = None
    ) -> None:
        self._logger = logger if logger else logging.getLogger("GurobiOptimizer")
        self._logger.info("Initializing GurobiOptimizer")
        self.instance = instance
        self._coverages = GuardCoverage(instance)
        self._witness_strategy = WitnessStrategy(
            instance, self._coverages, OptimizerParams()
        )
        self._dists = GuardDistances(instance, self._coverages)
        self._model = gp.Model()
        self._vars = _VarMap(instance, self._model)
        self.solution = None
        self.objective = 0
        self.upper_bound = math.inf
        self._build_objective()
        self._add_initial_witnesses()
        self._logger.info("Finished initializing GurobiOptimizer")

    def _add_initial_witnesses(self):
        for _witness, guards in self._witness_strategy.get_initial_witnesses():
            self._model.addConstr(gp.quicksum(self._vars.x(g) for g in guards) >= 1)

    def _build_objective(self):
        self._model.setObjective(self._vars.l(), gp.GRB.MAXIMIZE)

        def dist(g: int, g_: int) -> float:
            return self._dists.distance(g, g_)

        big_M = self._dists.max()
        for g, g_ in itertools.combinations(range(self.instance.num_positions()), 2):
            self._model.addConstr(
                self._vars.l()
                <= dist(g, g_) + big_M * (2 - self._vars.x(g) - self._vars.x(g_))
            )

    def get_opt_gap(self) -> float:
        if self.upper_bound == math.inf:
            return math.inf
        return (self.upper_bound - self.objective) / self.upper_bound

    def get_stats(self) -> typing.Dict[str, typing.Any]:
        return {
            "objective": self.objective,
            "upper_bound": self.upper_bound,
            "opt_gap": self.get_opt_gap(),
            "witness_stats": self._witness_strategy.get_stats(),
            "gurobi": {
                "status": self._model.Status,
                "sol_count": self._model.SolCount,
                "mip_gap": self._model.MIPGap,
                "obj_bound": self._model.ObjBound,
                "obj_val": self._model.ObjVal,
                "runtime": self._model.Runtime,
                "node_count": self._model.NodeCount,
                "time_in_callback": self._model.cbGet(GRB.Callback.RUNTIME),
            },
        }

    def solve(
        self, time_limit: float, opt_tol: float = 0.0001
    ) -> "GurobiOptimizer.Status":
        def callback(model: gp.Model, where: int) -> None:
            if where == gp.GRB.Callback.MIPSOL:
                solution = self._vars.get_guards(lambda x: model.cbGetSolution(x))
                new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(
                    solution
                )
                if new_witnesses:
                    for _witness, guards in new_witnesses:
                        model.cbLazy(gp.quicksum(self._vars.x(g) for g in guards) >= 1)
                else:
                    self.upper_bound = min(
                        self.upper_bound, model.cbGet(GRB.Callback.MIPSOL_OBJBND)
                    )
                    if self.objective <= model.cbGet(GRB.Callback.MIPSOL_OBJBST):
                        self.objective = model.cbGet(GRB.Callback.MIPSOL_OBJBST)
                        self.solution = solution
                    if len(solution) == 1:
                        self.solution = solution
                        self.objective = math.inf
            elif where == gp.GRB.Callback.MESSAGE:
                msg = model.cbGet(GRB.Callback.MSG_STRING)
                self._logger.info(msg)

        self._model.Params.MIPGap = (
            opt_tol  # Waring: This may differ from the definition of CP-SAT
        )
        self._model.Params.LogToConsole = 0
        self._model.Params.TimeLimit = time_limit
        self._model.Params.LazyConstraints = 1
        self._model.optimize(callback)
        if self._model.SolCount > 0:
            self.objective = self._model.ObjVal
            self.solution = self._vars.get_guards(lambda x: x.X)
            self.upper_bound = self._model.ObjBound
            if len(self.solution) == 1:
                self.objective = math.inf
                self.upper_bound = math.inf
                return self.Status.OPTIMAL
            if self._model.Status == GRB.OPTIMAL:
                return self.Status.OPTIMAL
            return self.Status.FEASIBLE
        # No solution found
        self.objective = math.inf
        self.solution = None
        return self.Status.UNKNOWN
