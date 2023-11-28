import itertools
import logging
import math
import typing
from enum import Enum

from .basic_sat_model import BasicSatModel
from .guard_distances import GuardDistances
from .instance import Instance
from .timer import Timer


class SearchStrategy(Enum):
    UP = 0
    DOWN = 1
    BINARY = 2


class DistanceOptimizer:
    def __init__(
        self,
        instance: Instance,
        guard_distances: GuardDistances,
        logger: logging.Logger,
    ) -> None:
        self._logger = logger
        self.instance = instance
        self.objective = 0.0
        self.upper_bound = math.inf
        self._sat_model = BasicSatModel(
            instance, logger=logger.getChild("BasicSatModel")
        )
        self._guard_distances = guard_distances
        self._coverage_constraints = []
        self.solution = list(range(instance.num_positions()))  # trivial solution
        self._k = 0.0
        self._stats = {
            "ks": [],
        }

    def add_upper_bound(self, upper_bound: float) -> None:
        self.upper_bound = min(self.upper_bound, upper_bound)
        assert (
            self.objective <= self.upper_bound
        ), f"{self.objective} <= {self.upper_bound}"

    def _solve_for_k(self, k: float, timer: Timer) -> bool:
        if self._k > k:
            # reset model
            self._logger.info("Resetting model because k got lowered...")
            self._sat_model.reset_constraints()
            for constraint in self._coverage_constraints:
                self._sat_model.add_coverage_constraint(constraint)
            self._k = 0.0
        assert self._k <= k
        self._logger.info("Prohibiting guard pairs for k=%f...", k)
        guards = list(range(self.instance.num_positions()))
        num_prohibited_pairs = 0
        for guard_a, guard_b in itertools.combinations(guards, 2):
            if self._k <= self._guard_distances.distance(guard_a, guard_b) < k:
                self._sat_model.prohibit_guard_pair(guard_a, guard_b)
                num_prohibited_pairs += 1
        self._k = k
        self._logger.info("Prohibited %d guard pairs.", num_prohibited_pairs)
        return self._sat_model.solve(timer.remaining())

    def _select_next_k(self, search_strategy: SearchStrategy) -> float:
        if search_strategy == SearchStrategy.UP:
            k = self._guard_distances.get_next_higher_distance(self.objective)
        elif search_strategy == SearchStrategy.DOWN:
            k = self._guard_distances.get_next_lower_distance(self.upper_bound)
            k = max(k, self._guard_distances.get_next_higher_distance(self.objective))
        else:
            assert search_strategy == SearchStrategy.BINARY
            k = (self.objective + self.upper_bound) / 2
            k = max(k, self._guard_distances.get_next_higher_distance(self.objective))
        k = min(k, self.upper_bound)
        self._stats["ks"].append(k)
        return k

    def _solve_for_k_with_callback(
        self,
        k: float,
        timer: Timer,
        callback: typing.Callable[[typing.List[int]], typing.List[typing.List[int]]],
    ) -> bool:
        # resolve model for k until the callback returns no further cuts
        feasible = self._solve_for_k(k, timer)
        # let the callback decide if it is really feasible
        cuts = callback(self._sat_model.get_solution()) if feasible else []
        while feasible and cuts:
            timer.check()
            for cut in cuts:
                self.add_coverage_constraint(cut)
            self._coverage_constraints += cuts
            feasible = self._sat_model.solve(timer.remaining())
            cuts = callback(self._sat_model.get_solution()) if feasible else []
        return feasible

    def add_coverage_constraint(self, vertices: typing.List[int]):
        assert all(0 <= i < self.instance.num_positions() for i in vertices)
        assert len(vertices) > 0
        self._sat_model.add_coverage_constraint(vertices)
        self._coverage_constraints.append(vertices)
        self._logger.debug("Added coverage constraint for %d vertices.", len(vertices))

    def get_opt_gap(self) -> float:
        if self.objective == 0.0:
            return math.inf
        return abs(self.objective - self.upper_bound) / self.objective

    def get_stats(self) -> typing.Dict[str, typing.Any]:
        stats = self._stats.copy()
        stats["solver"] = self._sat_model.get_stats()
        return stats

    def solve(
        self,
        timelimit: float = 900,
        search_strategy: SearchStrategy = SearchStrategy.BINARY,
        callback: typing.Optional[
            typing.Callable[[typing.List[int]], typing.List[typing.List[int]]]
        ] = None,
        timer: typing.Optional[Timer] = None,
        opt_tol: float = 0.0001,
    ) -> bool:
        if not callback:
            callback = lambda _: []  # noqa: E731
        timer = timer if timer is not None else Timer(timelimit)
        while self.get_opt_gap() > opt_tol:
            timer.check()
            k = self._select_next_k(search_strategy)  # next value to try
            assert (
                self.objective < k <= self.upper_bound
            ), f"{self.objective} < {k} <= {self.upper_bound}"
            feasible = self._solve_for_k_with_callback(k, timer, callback)
            if not feasible:
                self._logger.info("No solution found for k=%f.", k)
                next_lower_dist = self._guard_distances.get_next_lower_distance(k)
                self._logger.info(
                    "Next lower distance of k=%f: %f.", k, next_lower_dist
                )
                self.add_upper_bound(next_lower_dist)
                self._logger.info("Upper bound reduced to %f.", self.upper_bound)
                continue
            # if we got this far, we have a solution
            self._logger.info("Solution found for k=%f.", k)
            self.solution = self._sat_model.get_solution()
            self.objective = self._guard_distances.min_distance_of_guards(self.solution)
            self._logger.info(
                "Objective: %f/ Upper Bound: %f", self.objective, self.upper_bound
            )
        if self.objective == math.inf:
            feasible = self._solve_for_k_with_callback(math.inf, timer, callback)
            assert feasible
            self.solution = self._sat_model.get_solution()
            self.objective = self._guard_distances.min_distance_of_guards(self.solution)
        return True
