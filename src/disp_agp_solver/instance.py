import typing

from pyvispoly import Point, Polygon, PolygonWithHoles

Position = typing.Tuple[int, int]


class Instance:
    def __init__(
        self,
        positions: typing.List[Position],
        boundary: typing.List[int],
        holes: typing.Optional[typing.List[typing.List[int]]] = None,
    ) -> None:
        if holes is None:
            holes = []
        indices = set(boundary) | {i for hole in holes for i in hole}
        # check if boundary and holes are valid
        if min(indices) != 0 or max(indices) != len(positions) - 1:
            msg = "Invalid boundary or holes"
            raise ValueError(msg)
        self.positions = positions
        self.boundary = boundary
        self.holes = holes

    def num_holes(self) -> int:
        return len(self.holes)

    def num_positions(self) -> int:
        return len(self.positions)

    def as_cgal_position(self, i: int) -> Point:
        return Point(self.positions[i][0], self.positions[i][1])

    def as_cgal_polygon(self) -> PolygonWithHoles:
        boundary = Polygon([self.as_cgal_position(i) for i in self.boundary])
        holes = [
            Polygon([self.as_cgal_position(i) for i in hole]) for hole in self.holes
        ]
        if float(boundary.area()) <= 0 or not boundary.is_simple():
            msg = "Boundary is not valid"
            raise ValueError(msg)
        if any(float(hole.area()) >= 0 or not hole.is_simple() for hole in holes):
            msg = "Holes are not valid"
            raise ValueError(msg)
        return PolygonWithHoles(boundary, holes)
