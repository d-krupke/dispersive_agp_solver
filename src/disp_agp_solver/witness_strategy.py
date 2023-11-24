from .instance import Instance
from .guard_coverage import GuardCoverage
import typing
from pyvispoly import PolygonWithHoles, Point


class WitnessStrategy:
    def __init__(self, instance: Instance, guard_coverage: GuardCoverage, lazy=True) -> None:
        self.instance = instance
        self.guard_coverage = guard_coverage
        self.witnesses = []
        self.lazy = lazy

    def get_witnesses_for_area(
        self, area: PolygonWithHoles
    ) -> typing.List[typing.Tuple[Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        witnesses = []
        for witness in area.interior_sample_points():
            guards = self.guard_coverage.compute_guards_for_witness(witness)
            witnesses.append((witness, guards))
        assert witnesses, "Should not be empty."
        self.witnesses += witnesses
        return witnesses

    def get_initial_witnesses(
        self,
    ) -> typing.List[typing.Tuple[Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        witnesses = []
        for v in range(self.instance.num_positions()):
            visibility = self.guard_coverage.get_visibility_of_guard(v)
            guards = self.guard_coverage.compute_guards_within_polygon(visibility)
            witnesses.append((self.instance.as_cgal_position(v), guards))
        assert witnesses, "Should not be empty."
        self.witnesses += witnesses
        return witnesses

    def get_witnesses_for_guard_set(
        self, guards: typing.List[int]
    ) -> typing.List[typing.Tuple[Point, typing.List[int]]]:
        """
        Add witnesses to the given polygon.
        """
        witnesses = []
        missing_areas = self.guard_coverage.compute_uncovered_area(guards)
        for area in missing_areas:
            witnesses += self.get_witnesses_for_area(area)
        assert witnesses or not missing_areas, "Should not be empty."
        return witnesses

    def __call__(self, guards: typing.List[int]) -> typing.List[typing.List[int]]:
        if not self.lazy:
            return []
        witnesses = self.get_witnesses_for_guard_set(guards)
        return [w[1] for w in witnesses]
