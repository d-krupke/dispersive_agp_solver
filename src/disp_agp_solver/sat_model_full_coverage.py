import typing

import pyvispoly

from .instance import Instance
from .sat_model import SatModel
from .timer import Timer


class SatModelWithFullCoverage:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance
        n = instance.num_positions()
        self._vis_calc = pyvispoly.VisibilityPolygonCalculator(
            instance.as_cgal_polygon()
        )
        guard_pos = [instance.as_cgal_position(i) for i in range(n)]
        self.vis_polys_of_guards = [
            pyvispoly.PolygonWithHoles(self._vis_calc.compute_visibility_polygon(p))
            for p in guard_pos
        ]
        self._sat_model = SatModel(instance)
        self.witnesses = []

    def _compute_missing_areas(self, guards) -> typing.List[pyvispoly.PolygonWithHoles]:
        """
        Compute the missing area of the current guard set.
        """
        missing_area = [self.instance.as_cgal_polygon()]
        coverages = [self.vis_polys_of_guards[i] for i in guards]
        for coverage in coverages:
            assert all(isinstance(p, pyvispoly.PolygonWithHoles) for p in missing_area)
            assert isinstance(coverage, pyvispoly.PolygonWithHoles)
            # difference is always a list of polygons as it can split a polygon into multiple parts
            missing_area = sum((poly.difference(coverage) for poly in missing_area), [])
        return missing_area

    def _get_guards_for_witness(self, witness: pyvispoly.Point) -> typing.List[int]:
        """
        Compute which vertex guard can see the given witness.
        """
        vis_poly = self._vis_calc.compute_visibility_polygon(witness)
        guards = [
            i
            for i in range(self.instance.num_positions())
            if vis_poly.contains(self.instance.as_cgal_position(i))
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
            guards = self._get_guards_for_witness(witness)
            self.witnesses.append((witness, guards))
            witnesses.append((witness, guards))
            self._sat_model.add_coverage_constraint(guards)
        assert witnesses, "Should not be empty."
        return witnesses

    def solve(
        self,
        timelimit: float = 900,
        on_iteration: typing.Optional[typing.Callable] = None,
    ) -> bool:
        timer = Timer(timelimit)
        feasible = self._sat_model.solve(timer.remaining())
        if not feasible:
            return False
        guards = self._sat_model.get_solution()
        missing_areas = self._compute_missing_areas(guards)
        while missing_areas:
            witnesses = []
            for missing_area in missing_areas:
                witnesses += self._add_witnesses_to_area(missing_area)
                assert not set(witnesses[-1][1])&set(guards), "Redundant witness."
            if on_iteration is not None:
                on_iteration(guards, witnesses, missing_areas)
            feasible = self._sat_model.solve(timer.remaining())
            if not feasible:
                return False
            guards = self._sat_model.get_solution()
            missing_areas = self._compute_missing_areas(guards)
        return True

    def prohibit_guard_pair(self, i: int, j: int) -> None:
        self._sat_model.prohibit_guard_pair(i, j)

    def get_solution(self) -> typing.List[int]:
        return self._sat_model.get_solution()
