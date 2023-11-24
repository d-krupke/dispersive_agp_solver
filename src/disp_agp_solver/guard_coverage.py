import typing

from pyvispoly import Point, Polygon, PolygonWithHoles, VisibilityPolygonCalculator

from .instance import Instance


class GuardCoverage:
    """
    Computes the visibility polygons of all guards and can compute the missing area of a set of guards.
    """

    def __init__(self, instance: Instance) -> None:
        self._instance = instance
        self._visibility_polygon_calculator = VisibilityPolygonCalculator(
            instance.as_cgal_polygon()
        )
        self._vis_polys = self._compute_visibilities()

    def _compute_visibilities(self) -> typing.List[Polygon]:
        return [
            PolygonWithHoles(
                self._visibility_polygon_calculator.compute_visibility_polygon(
                    self._instance.as_cgal_position(i)
                )
            )
            for i in range(self._instance.num_positions())
        ]

    def can_guards_see_each_other(self, guard_a: int, guard_b: int) -> bool:
        return self.get_visibility_of_guard(guard_a).contains(
            self._instance.as_cgal_position(guard_b)
        )

    def get_visibility_of_guard(self, guard: int):
        return self._vis_polys[guard]

    def compute_uncovered_area(
        self, guards: typing.List[int]
    ) -> typing.List[PolygonWithHoles]:
        missing_area = [self._instance.as_cgal_polygon()]
        coverages = [self.get_visibility_of_guard(guard) for guard in guards]
        for coverage in coverages:
            assert all(isinstance(p, PolygonWithHoles) for p in missing_area)
            assert isinstance(coverage, PolygonWithHoles)
            # difference is always a list of polygons as it can split a polygon into multiple parts
            missing_area = sum((poly.difference(coverage) for poly in missing_area), [])
        return missing_area

    def compute_guards_within_polygon(self, poly: Polygon) -> typing.List[int]:
        """
        Compute which vertex guard can see the given witness.
        """
        guards = [
            i
            for i in range(self._instance.num_positions())
            if poly.contains(self._instance.as_cgal_position(i))
        ]
        return guards

    def compute_guards_for_witness(self, witness: Point) -> typing.List[int]:
        """
        Compute which vertex guard can see the given witness.
        """
        vis_poly = self._visibility_polygon_calculator.compute_visibility_polygon(
            witness
        )
        guards = self.compute_guards_within_polygon(vis_poly)
        assert guards, "Should not be empty."
        return guards
