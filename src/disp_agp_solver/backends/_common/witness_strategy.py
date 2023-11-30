"""
This file implements the witness strategy for the dispersion AGP solver.
It can be used for different approaches.
"""
import typing

from pyvispoly import Point, PolygonWithHoles

from .guard_coverage import GuardCoverage
from disp_agp_solver.instance import Instance


class WitnessStrategy:
    def __init__(
        self, instance: Instance, guard_coverage: GuardCoverage, lazy: bool = True, add_all_vertices_as_witnesses: bool = True
    ) -> None:
        self.instance = instance
        self.guard_coverage = guard_coverage
        self.witnesses = []
        self.lazy = lazy
        self.add_all_vertices_as_witnesses = add_all_vertices_as_witnesses
        self._stats = {
            "num_initial_witnesses": 0,
            "num_area_calls": 0,
            "num_guard_set_calls": 0,
            "num_guard_set_calls_with_witnesses": 0,
            "num_direct_calls": 0,
        }

    def get_witnesses_for_area(
        self, area: PolygonWithHoles
    ) -> typing.List[typing.Tuple[Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        self._stats["num_area_calls"] += 1
        witnesses = []
        for witness in area.interior_sample_points():
            guards = self.guard_coverage.compute_guards_for_witness(witness)
            witnesses.append((witness, guards))
        assert witnesses, "Should not be empty."
        self.witnesses += witnesses
        return witnesses

    def get_initial_witnesses(
        self,
    ) -> typing.List[typing.Tuple[typing.Optional[Point], typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        if not self.add_all_vertices_as_witnesses:
            trivial_constraint = list(range(self.instance.num_positions()))
            self.witnesses += trivial_constraint
            return [(None, trivial_constraint)]
        witnesses = []
        for v in range(self.instance.num_positions()):
            visibility = self.guard_coverage.get_visibility_of_guard(v)
            guards = self.guard_coverage.compute_guards_within_polygon(visibility)
            witnesses.append((self.instance.as_cgal_position(v), guards))
        assert witnesses, "Should not be empty."
        self.witnesses += witnesses
        self._stats["num_initial_witnesses"] += len(witnesses)
        return witnesses

    def get_witnesses_for_guard_set(
        self, guards: typing.List[int]
    ) -> typing.List[typing.Tuple[Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        self._stats["num_guard_set_calls"] += 1
        witnesses = []
        missing_areas = self.guard_coverage.compute_uncovered_area(guards)
        for area in missing_areas:
            witnesses += self.get_witnesses_for_area(area)
        if witnesses:
            self._stats["num_guard_set_calls_with_witnesses"] += 1
        assert witnesses or not missing_areas, "Should not be empty."
        return witnesses

    def get_stats(self) -> typing.Dict[str, typing.Any]:
        stats = {
            "num_witnesses": len(self.witnesses),
        }
        stats.update(self._stats)
        return stats

    def __call__(self, guards: typing.List[int]) -> typing.List[typing.List[int]]:
        self._stats["num_direct_calls"] += 1
        if not self.lazy:
            return []
        witnesses = self.get_witnesses_for_guard_set(guards)
        return [w[1] for w in witnesses]
