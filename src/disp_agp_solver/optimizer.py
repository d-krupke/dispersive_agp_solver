from .instance import Instance
from enum import Enum
import logging
import typing
from pyvispoly import Point

import math
from .distance_optimizer import DistanceOptimizer
from .guard_distances import GuardDistances
from .witness_strategy import WitnessStrategy
from .guard_coverage import GuardCoverage
from .timer import Timer

class SatBasedOptimizer:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(self, instance: Instance, logger: typing.Optional[logging.Logger]) -> None:
        self._logger = logger if logger else logging.getLogger("DispAgpSolver")
        self._guard_coverage = GuardCoverage(instance)
        self._guard_distances = GuardDistances(instance, self._guard_coverage)
        self.instance = instance
        self.upper_bound = math.inf
        self.objective = 0
        self.solution = list(range(instance.num_positions()))

    def add_upper_bound(self, upper_bound: float) -> None:
        self.upper_bound = min(self.upper_bound, upper_bound)
        self._logger.info("Setting upper bound to %f", self.upper_bound)

    def _compute_optimal_for_witness_set(self, witnesses: typing.List[typing.Tuple[Point, typing.List[int]]], timer: Timer) -> typing.Tuple[typing.List[int], float]:
        self._logger.info("Computing optimal solution for %d witnesses...", len(witnesses))
        dist_optimizer = DistanceOptimizer(self.instance, logger=self._logger, guard_distances=self._guard_distances)
        dist_optimizer.add_upper_bound(self.upper_bound)
        for witness, guards in witnesses:
            dist_optimizer.add_coverage_constraint(guards)
        dist_optimizer.solve(timer=timer)
        self._logger.info("Found optimal solution with objective %f for witness set", dist_optimizer.objective)
        self.add_upper_bound(dist_optimizer.objective)
        return dist_optimizer.solution, dist_optimizer.objective

    def solve(self, time_limit: float = 900) -> "SatBasedOptimizer.Status":
        try:
            witness_strategy = WitnessStrategy(self.instance, guard_coverage=self._guard_coverage)
            timer = Timer(time_limit)
            solution, obj = self._compute_optimal_for_witness_set(witness_strategy.get_initial_witnesses(), timer)
            self.upper_bound = obj
            self._logger.info("Setting upper bound to %f", self.upper_bound)
            new_witnesses = witness_strategy.get_witnesses_for_guard_set(solution)
            while new_witnesses:
                self._logger.info("Adding %d witnesses to cover missing area...", len(new_witnesses))
                solution, obj = self._compute_optimal_for_witness_set(witness_strategy.witnesses, timer)
                new_witnesses = witness_strategy.get_witnesses_for_guard_set(solution)
                assert not any(set(w[1])&set(solution) for w in new_witnesses), "Redundant witness."
            self.solution = solution
            self.objective = obj
            self._logger.info("Found solution with objective %f", self.objective)
        except TimeoutError:
            self._logger.info("Timelimit reached.")
            if self.objective == self.upper_bound:
                return SatBasedOptimizer.Status.OPTIMAL
            if self.solution is not None:
                return SatBasedOptimizer.Status.FEASIBLE
        return SatBasedOptimizer.Status.UNKNOWN