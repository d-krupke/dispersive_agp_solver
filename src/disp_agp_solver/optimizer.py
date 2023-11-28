import logging
import math
import typing
from enum import Enum

from pyvispoly import Point, PolygonWithHoles

from .distance_optimizer import DistanceOptimizer, SearchStrategy
from .guard_coverage import GuardCoverage
from .guard_distances import GuardDistances
from .instance import Instance
from .params import OptimizerParams
from .timer import Timer
from .witness_strategy import WitnessStrategy


class OptimizerObserver:
    def on_coverage_iteration(
        self,
        guards: typing.List[int],
        witnesses: typing.List[typing.Tuple[Point, typing.List[int]]],
        missing_areas: typing.List[PolygonWithHoles],
    ) -> None:
        pass

    def on_new_witnesses(
            self,
            guards: typing.List[int],
            new_witnesses: typing.List[typing.Tuple[Point, typing.List[int]]],
    ) -> None:
        pass

    def on_new_solution(
        self,
        guards: typing.List[int],
        objective: float,
        obj_defining_guards: typing.List[int],
        witnesses: typing.List[typing.Tuple[Point, typing.List[int]]],
    ) -> None:
        pass


class SatBasedOptimizer:
    class Status(Enum):
        OPTIMAL = 0
        FEASIBLE = 1
        UNKNOWN = 2

    def __init__(
        self,
        instance: Instance,
        logger: typing.Optional[logging.Logger],
        params: typing.Optional[OptimizerParams] = None,
    ) -> None:
        self._logger = logger if logger else logging.getLogger("DispAgpSolver")
        self.params = params if params else OptimizerParams()
        self._logger.info("Setting up coverage calculator...")
        self._guard_coverage = GuardCoverage(instance)
        self._logger.info("Setting up guard distances...")
        self._guard_distances = GuardDistances(instance, self._guard_coverage)
        self._logger.info("Setting up witness strategy...")
        self._witness_strategy = WitnessStrategy(
            instance, guard_coverage=self._guard_coverage, params=self.params
        )
        self.observer = OptimizerObserver()
        self.instance = instance
        self.upper_bound = math.inf
        self.objective = 0
        self.solution = list(range(instance.num_positions()))
        self._logger.info("Ready for optimization.")

    def add_upper_bound(self, upper_bound: float) -> None:
        self.upper_bound = min(self.upper_bound, upper_bound)
        self._logger.info("Setting upper bound to %f", self.upper_bound)

    def _compute_optimal_for_witness_set(
        self,
        witnesses: typing.List[typing.Tuple[Point, typing.List[int]]],
        timer: Timer,
        search_strategy: SearchStrategy,
    ) -> typing.Tuple[typing.List[int], float]:
        self._logger.info(
            "Computing optimal solution for %d witnesses...", len(witnesses)
        )
        dist_optimizer = DistanceOptimizer(
            self.instance, logger=self._logger, guard_distances=self._guard_distances
        )
        try:
            dist_optimizer.add_upper_bound(self.upper_bound)
            for _, guards in witnesses:
                dist_optimizer.add_coverage_constraint(guards)
            dist_optimizer.solve(
                timer=timer,
                callback=self._witness_strategy,
                search_strategy=search_strategy,
            )
            self._logger.info(
                "Found optimal solution with objective %f for witness set",
                dist_optimizer.objective,
            )
            self.add_upper_bound(dist_optimizer.upper_bound)
        except TimeoutError as te:
            self.add_upper_bound(dist_optimizer.upper_bound)
            raise
        return dist_optimizer.solution, dist_optimizer.objective

    def solve(self, time_limit: float = 900) -> "SatBasedOptimizer.Status":
        try:
            timer = Timer(time_limit)
            solution, obj = self._compute_optimal_for_witness_set(
                self._witness_strategy.get_initial_witnesses(),
                timer,
                search_strategy=self.params.search_strategy_start,
            )
            self.upper_bound = obj
            self._logger.info("Setting upper bound to %f", self.upper_bound)
            new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(solution)
            while new_witnesses:
                self._logger.info(
                    "Adding %d witnesses to cover missing area...", len(new_witnesses)
                )
                self.observer.on_new_witnesses(solution, new_witnesses)
                solution, obj = self._compute_optimal_for_witness_set(
                    self._witness_strategy.witnesses,
                    timer,
                    search_strategy=self.params.search_strategy_iteration,
                )
                new_witnesses = self._witness_strategy.get_witnesses_for_guard_set(
                    solution
                )
                assert not any(
                    set(w[1]) & set(solution) for w in new_witnesses
                ), "Redundant witness."
            self.solution = solution
            self.objective = obj
            self._logger.info("Found solution with objective %f", self.objective)
            return SatBasedOptimizer.Status.OPTIMAL
        except TimeoutError:
            self._logger.info("Timelimit reached.")
            if self.objective == self.upper_bound:
                return SatBasedOptimizer.Status.OPTIMAL
            if self.solution is not None:
                return SatBasedOptimizer.Status.FEASIBLE
        return SatBasedOptimizer.Status.UNKNOWN
