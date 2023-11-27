from ortools.sat.python import cp_model
import typing
import itertools
import math
from enum import Enum
from .guard_coverage import GuardCoverage
from .instance import Instance
from .witness_strategy import WitnessStrategy
from .guard_distances import GuardDistances
from .params import OptimizerParams
from .timer import Timer


class _VarMap:
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

    def l(self) -> cp_model.IntVar:
        return self._l

    def get_guards(
        self, get_val: typing.Callable[[cp_model.IntVar], int]
    ) -> typing.List[int]:
        return [g for g, x in enumerate(self._vars) if get_val(x)]


class _CpSatModel:
    def __init__(
        self, instance: Instance, dists: GuardDistances, scaling_factor: int = 10_000
    ) -> None:
        self.instance = instance
        self.model = cp_model.CpModel()
        self.scaling_factor = scaling_factor
        self._vars = _VarMap(
            instance.num_positions(), self.model, round(dists.max() * scaling_factor+1)
        )
        self._dists = dists
        self._build_objective()
        self.upper_bound = math.inf

    def _build_objective(self):
        self.model.Maximize(self._vars.l())

        def dist(g: int, g_: int) -> float:
            return round(self._dists.distance(g, g_) * self.scaling_factor)

        for g, g_ in itertools.combinations(range(self.instance.num_positions()), 2):
            self.model.Add(self._vars.l() <= dist(g, g_)).OnlyEnforceIf(
                self._vars.y(g, g_)
            )

    def add_witness(self, guards: typing.List[int]):
        self.model.AddBoolOr([self._vars.x(g) for g in guards])

    def add_upper_bound(self, d: float):
        self.model.Add(self._vars.l() <= round(d * self.scaling_factor))

    def solve(self, timer: Timer) -> typing.Tuple[float, typing.List[int]]:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timer.remaining()
        solver.parameters.log_search_progress = True
        status = solver.Solve(self.model)
        self.upper_bound = min(
            self.upper_bound, solver.ObjectiveValue() / self.scaling_factor
        )
        if status == cp_model.OPTIMAL:
            solution = self._vars.get_guards(lambda x: solver.Value(x))
            if len(solution) == 1:
                return math.inf, solution
            return solver.ObjectiveValue() / self.scaling_factor, solution
        elif status == cp_model.FEASIBLE or status == cp_model.UNKNOWN:
            raise TimeoutError()
        raise ValueError(f"Unexpected status {status}")


class CpSatOptimizer:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(self, instance: Instance):
        self.instance = instance
        self._guard_coverage = GuardCoverage(instance)
        self._dists = GuardDistances(instance, self._guard_coverage)
        self._witness_strategy = WitnessStrategy(
            instance, self._guard_coverage, OptimizerParams()
        )
        self._model = _CpSatModel(instance, self._dists)
        self.solution = None
        self.upper_bound = math.inf
        self.objective = 0

    def solve(self, time_limit: float):
        try:
            timer = Timer(time_limit)
            for witness, guards in self._witness_strategy.get_initial_witnesses():
                self._model.add_witness(guards)
            obj, solution = self._model.solve(timer)
            self.upper_bound = obj
            new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(solution)
            while new_witnesses:
                timer.check()
                for witness, guards in new_witnesses:
                    self._model.add_witness(guards)
                self._model.add_upper_bound(self.upper_bound)
                obj, solution = self._model.solve(timer)
                self.upper_bound = obj
                new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(solution)
            self.solution = solution
            if len(self.solution) == 1:
                self.objective = math.inf
            self.objective = obj
            return self.Status.OPTIMAL
        except TimeoutError:
            if self.solution is not None:
                return self.Status.FEASIBLE
        return self.Status.UNKNOWN
