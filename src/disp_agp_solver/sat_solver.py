"""
This file implements an exact solver for the dispersion AGP problem.
The used SAT-formula is in a separate file.
"""

import itertools
import logging
import typing

import pyvispoly

from .guard_coverage import GuardCoverage
from .guard_distances import GuardDistances
from .instance import Instance
from .sat_model_full_coverage import SatModelWithFullCoverage
from .timer import Timer


class DispAgpSolverObserver:
    def on_coverage_iteration(
        self,
        guards: typing.List[int],
        witnesses: typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]],
        missing_areas: typing.List[pyvispoly.PolygonWithHoles],
    ) -> None:
        pass

    def on_new_solution(
        self,
        guards: typing.List[int],
        objective: float,
        closest_pair: typing.Tuple[int, int],
        witnesses: typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]],
    ) -> None:
        pass


class DispAgpSolver:
    """
    This class implements an exact solver for the dispersion AGP problem.

    Basic usage:
    >>> instance = load_instance()
    >>> solver = DispAgpSolver(instance)
    >>> solver.optimize(timelimit=900)
    [0, 1, 5, 6, 7, 8, 9]
    >>> solver.objective
    4.3

    """

    def __init__(
        self,
        instance: Instance,
        solver: str = "Glucose4",
        logger: typing.Optional[logging.Logger] = None,
    ) -> None:
        if logger is None:
            self._logger = logging.getLogger("DispAgpSolver")
        else:
            self._logger = logger
        self._instance = instance
        n = instance.num_positions()
        self._logger.info("Building basic model...")
        guard_coverage = GuardCoverage(instance)
        self._sat_model = SatModelWithFullCoverage(
            instance, guard_coverage=guard_coverage, solver=solver, logger=self._logger
        )
        self._sat_model.add_witnesses_at_vertices()
        self.guards = list(range(n))
        self._logger.info("Setting up geodesic distances...")
        dist_calc = GuardDistances(instance, guard_coverage)
        self._logger.info("Computing distances of all pairs...")
        dist_calc.compute_all_distances()
        self._logger.info("Sorting distances...")
        self._distances = [
            ((i, j), dist_calc.distance(i, j))
            for i, j in itertools.combinations(range(n), 2)
        ]
        self._distances.sort(key=lambda x: -x[1])
        self.objective = self._distances[-1][1]
        self._logger.info("Initial objective is %d", self.objective)
        self.closest_pair = self._distances[-1][0]
        self.observer = DispAgpSolverObserver()
        self._stats = []

    def _propagate_distances(self) -> None:
        """
        Propagate distance constraints.
        """
        (i, j), d = self._distances[-1]
        while i not in self.guards or j not in self.guards:
            self._distances.pop()
            self._sat_model.prohibit_guard_pair(i, j)
            (i, j), d = self._distances[-1]
        if not self._distances:
            self.objective = float("inf")
            assert len(self.guards) == 1
            self.closest_pair = (self.guards[0], self.guards[0])
        else:
            self.objective = self._distances[-1][1]
            self.closest_pair = self._distances[-1][0]

    def get_witnesses(
        self,
    ) -> typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]]:
        return self._sat_model.witnesses

    def _log_statistics(self, guards, objective, feasible, time):
        self._stats.append(
            {
                "num_guards": len(guards) if guards is not None else 0,
                "objective": objective,
                "feasible": feasible,
                "sat_stats": self._sat_model.get_statistics(),
                "time": time,
            }
        )

    def get_statistics(self):
        return list(self._stats)

    def optimize(self, timelimit: float = 900) -> typing.Optional[typing.List[int]]:
        """
        Return a list of indices of guards that should be selected.
        """
        timer = Timer(timelimit)
        feasible = self._sat_model.solve(
            timelimit=timer.remaining(),
            on_iteration=self.observer.on_coverage_iteration,
        )
        self._log_statistics(self.guards, self.objective, feasible, timer.time())
        while feasible and self._distances:
            self.observer.on_new_solution(
                self.guards, self.objective, self.closest_pair, self.get_witnesses()
            )
            self.guards = self._sat_model.get_solution()
            # based on the best feasible solution, we can directly prohibit
            # all pairs that would create a worse solution, speeding up the search.
            self._propagate_distances()
            if not self._distances:
                break  # single guard left, infinite objective
            # enforce a shorter distance and resolve
            (i, j), d = self._distances.pop()
            self._sat_model.prohibit_guard_pair(i, j)
            timer.check()
            feasible = self._sat_model.solve(
                timelimit=timer.time(),
                on_iteration=self.observer.on_coverage_iteration,
            )
            self._log_statistics(
                self.guards, self.objective, feasible, timer.remaining()
            )
        return self.guards
