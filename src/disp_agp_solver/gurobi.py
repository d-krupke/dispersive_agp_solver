import typing
import itertools
import math
import gurobipy as gp
from gurobipy import GRB
from enum import Enum
from .guard_coverage import GuardCoverage
from .instance import Instance
from .witness_strategy import WitnessStrategy
from .guard_distances import GuardDistances
from .params import OptimizerParams
from .timer import Timer

class _VarMap:
    def __init__(self, instance :Instance, model: gp.Model) -> None:
        self._vars = [model.addVar(vtype=gp.GRB.BINARY, name=f"x_{i}") for i in range(instance.num_positions())]
        self._l = model.addVar(vtype=gp.GRB.CONTINUOUS, name="l")
    
    def x(self, g: int) -> gp.Var:
        return self._vars[g]
    
    def l(self) -> gp.Var:
        return self._l
    
    def get_guards(self, get_val: typing.Callable[[gp.Var], int]) -> typing.List[int]:
        return [g for g, x in enumerate(self._vars) if get_val(x)]

class GurobiSolver:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(self, instance: Instance) -> None:
        self.instance = instance
        self._coverages = GuardCoverage(instance)
        self._witness_strategy = WitnessStrategy(instance, self._coverages, OptimizerParams())
        self._dists = GuardDistances(instance, self._coverages)
        self._model = gp.Model()
        self._vars = _VarMap(instance, self._model)
        self.solution = None
        self.objective = 0
        self.upper_bound = math.inf
        self._build_objective()
        self._add_initial_witnesses()

    def _add_initial_witnesses(self):
        for witness, guards in self._witness_strategy.get_initial_witnesses():
            self._model.addConstr(gp.quicksum(self._vars.x(g) for g in guards) >= 1)

    def _build_objective(self):
        self._model.setObjective(self._vars.l(), gp.GRB.MAXIMIZE)

        def dist(g: int, g_: int) -> float:
            return self._dists.distance(g, g_)

        big_M = self._dists.max()
        for g, g_ in itertools.combinations(range(self.instance.num_positions()), 2):
            self._model.addConstr(self._vars.l() <= dist(g, g_) + big_M * (2 - self._vars.x(g) - self._vars.x(g_)))


    def solve(self, time_limit: float) -> "GurobiSolver.Status":
        def callback(model: gp.Model, where: int) -> None:
            if where == gp.GRB.Callback.MIPSOL:
                solution = self._vars.get_guards(lambda x: model.cbGetSolution(x))
                new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(solution)
                if new_witnesses:
                    for witness, guards in new_witnesses:
                        model.cbLazy(gp.quicksum(self._vars.x(g) for g in guards) >= 1)
                else:
                    self.upper_bound = min(self.upper_bound, model.cbGet(GRB.Callback.MIPSOL_OBJBND))
                    if self.objective <= model.cbGet(GRB.Callback.MIPSOL_OBJBST):
                        self.objective = model.cbGet(GRB.Callback.MIPSOL_OBJBST)
                        self.solution = solution
                    if len(solution) == 1:
                        self.solution = solution
                        self.objective = math.inf

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
        else:
            self.objective = math.inf
            self.solution = None
            return self.Status.UNKNOWN
