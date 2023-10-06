"""
This file implements an exact solver for the dispersion AGP problem.
The used SAT-formula is in a separate file.
"""

import typing
import itertools
from pysat.solvers import Glucose4
import typing
from .instance import Instance
from .geodesic_distances import GeodesicDistances
import pyvispoly
from .timer import Timer

from .sat_model_full_coverage import SatModelWithFullCoverage


class DispAgpSolverObserver:

    def on_coverage_iteration(
        self,
        guards: typing.List[int],
        witnesses: typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]],
        missing_areas: typing.List[pyvispoly.PolygonWithHoles],
    ):
        pass


    def on_new_solution(
        self,
        guards: typing.List[int],
        objective: float,
        closest_pair: typing.Tuple[int, int],
        witnesses: typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]],
    ):
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

    def __init__(self, instance: Instance) -> None:
        self._instance = instance
        n = instance.num_positions()
        self._sat_model = SatModelWithFullCoverage(instance)
        self.guards = list(range(n))
        dist_calc = GeodesicDistances(instance)
        self._distances = [
            ((i, j), dist_calc.distance(i, j))
            for i, j in itertools.combinations(range(n), 2)
        ]
        self._distances.sort(key=lambda x: -x[1])
        self.objective = self._distances[-1][1]
        self.closest_pair = self._distances[-1][0]
        self.observer = DispAgpSolverObserver()
    
    def _propagate_distances(self):
        """
        Propagate distance constraints.
        """
        (i,j), d = self._distances[-1]
        while i not in self.guards or j not in self.guards:
            self._distances.pop()
            self._sat_model.prohibit_guard_pair(i, j)
            (i,j), d = self._distances[-1]
        if not self._distances:
            self.objective = float("inf")
            assert len(self.guards) == 1
            self.closest_pair = (self.guards[0], self.guards[0])
        else:
            self.objective = self._distances[-1][1]
            self.closest_pair = self._distances[-1][0]

    def get_witnesses(self):
        return self._sat_model.witnesses

    def optimize(self, timelimit: float = 900) -> typing.Optional[typing.List[int]]:
        """
        Return a list of indices of guards that should be selected.
        """
        timer = Timer(timelimit)
        feasible = self._sat_model.solve(timelimit=timer.remaining(),
                                         on_iteration=self.observer.on_coverage_iteration)
        while feasible and self._distances:
            self.observer.on_new_solution(self.guards, self.objective, self.closest_pair, self.get_witnesses())
            self.guards = self._sat_model.get_solution()
            self._propagate_distances()
            if not self._distances:
                break  # single guard left, infinite objective
            # enforce a shorter distance and resolve
            (i,j), d = self._distances.pop()
            self._sat_model.prohibit_guard_pair(i, j)
            feasible = self._sat_model.solve(timelimit=timer.remaining(),
                                    on_iteration=self.observer.on_coverage_iteration)
        return self.guards
