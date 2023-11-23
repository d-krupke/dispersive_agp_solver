import typing
import logging
import pyvispoly

from .instance import Instance
from .sat_model import SatModel
from .timer import Timer
from .guard_coverage import GuardCoverage

class SatModelWithFullCoverage:
    def __init__(self, instance: Instance, guard_coverage: typing.Optional[GuardCoverage] = None, solver: str = "Glucose4", logger: typing.Optional[logging.Logger]=None) -> None:
        self.instance = instance
        if logger is None:
            self._logger = logging.getLogger("DispAgpFullCoverageSolver")
        else:
            self._logger = logger
        self._logger.info("Building basic full coverage model...")
        self._guard_coverage = guard_coverage if guard_coverage else GuardCoverage(instance)
        self._sat_model = SatModel(instance, solver=solver, logger=self._logger)
        self.witnesses = []
        self._num_prohibited_pairs = 0
        self._stats = []
        self._logger.info("Basic full coverage model built.")

    def add_witnesses_at_vertices(self) -> None:
        self._logger.info("Adding witnesses at vertices...")
        for v in range(self.instance.num_positions()):
            visibility = self._guard_coverage.get_visibility_of_guard(v)
            guards = self._guard_coverage.compute_guards_within_polygon(visibility)
            self.witnesses.append((self.instance.as_cgal_position(v), guards))
            self._sat_model.add_coverage_constraint(guards)

    def _get_guards_for_witness_visibility(self, visibility_poly: pyvispoly.Polygon) -> typing.List[int]:
        """
        Compute which vertex guard can see the given witness.
        """
        guards = [
            i
            for i in range(self.instance.num_positions())
            if visibility_poly.contains(self.instance.as_cgal_position(i))
        ]
        assert guards, "Should not be empty."
        return guards


    def _add_witnesses_to_area(
        self, poly: pyvispoly.PolygonWithHoles
    ) -> typing.List[typing.Tuple[pyvispoly.Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        witnesses = []
        for witness in poly.interior_sample_points():
            guards = self._guard_coverage.compute_guards_for_witness(witness)
            self.witnesses.append((witness, guards))
            witnesses.append((witness, guards))
            self._sat_model.add_coverage_constraint(guards)
        assert witnesses, "Should not be empty."
        return witnesses
    
    def _log_statistics(self, guards, feasible, time, missing_areas):
        self._stats.append({
            "num_guards": len(guards) if guards else None,
            "num_witnesses": len(self.witnesses) if guards is not None else 0,
            "num_prohibited_pairs": self._num_prohibited_pairs,
            "feasible": feasible,
            "sat_stats": self._sat_model.get_statistics(),
            "remaining_time": time,
            "num_missing_areas": len(missing_areas) if missing_areas is not None else 0,
        })

    def get_statistics(self):
        return list(self._stats)

    def solve(
        self,
        timelimit: float = 900,
        on_iteration: typing.Optional[typing.Callable] = None,
    ) -> bool:
        timer = Timer(timelimit)
        timer.check()
        feasible = self._sat_model.solve(timer.remaining())
        if not feasible:
            self._log_statistics(None, feasible, timer.remaining(), None)
            return False
        guards = self._sat_model.get_solution()
        self._logger.info("Computing missing areas...")
        missing_areas = self._guard_coverage.compute_uncovered_area(guards)
        self._log_statistics(guards, feasible, timer.remaining(), missing_areas)
        while missing_areas:
            witnesses = []
            self._logger.info("Adding witnesses to missing areas...")
            for missing_area in missing_areas:
                witnesses += self._add_witnesses_to_area(missing_area)
                assert not set(witnesses[-1][1])&set(guards), "Redundant witness."
            if on_iteration is not None:
                on_iteration(guards, witnesses, missing_areas)
            feasible = self._sat_model.solve(timer.remaining())
            if not feasible:
                self._log_statistics(None, feasible, timer.remaining(), None)
                return False
            guards = self._sat_model.get_solution()
            self._logger.info("Computing missing areas...")
            missing_areas = self._guard_coverage.compute_uncovered_area(guards)
            self._log_statistics(guards, feasible, timer.remaining(), missing_areas)
        return True

    def prohibit_guard_pair(self, i: int, j: int) -> None:
        self._num_prohibited_pairs += 1
        self._sat_model.prohibit_guard_pair(i, j)

    def get_solution(self) -> typing.List[int]:
        return self._sat_model.get_solution()
