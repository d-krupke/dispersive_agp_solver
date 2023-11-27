"""
This code computes the geodesic distances between all pairs of positions in an instance.
It is based on the visibility polygon calculator from the pyvispoly package.
It is a well known result that the geodesic distance between two points in a polygon
can be computed purely by connecting all vertices that can view each other and then
computing the shortest path between the two points in the resulting graph.
"""

import itertools
import math
import typing

import networkx as nx

from .guard_coverage import GuardCoverage
from .instance import Instance


class GuardDistances:
    def __init__(
        self, instance: Instance, guard_coverage: typing.Optional[GuardCoverage]
    ) -> None:
        guard_coverage = guard_coverage if guard_coverage else GuardCoverage(instance)
        self._graph = nx.Graph()
        self._graph.add_nodes_from(range(instance.num_positions()))
        for i in range(instance.num_positions()):
            for j in range(i + 1, instance.num_positions()):
                if guard_coverage.can_guards_see_each_other(i, j):
                    dist = math.sqrt(
                        (instance.positions[i][0] - instance.positions[j][0]) ** 2
                        + (instance.positions[i][1] - instance.positions[j][1]) ** 2
                    )
                    self._graph.add_edge(i, j, weight=dist)
        if not nx.is_connected(self._graph):
            msg = "Instance is not connected"
            raise ValueError(msg)
        self._apsp = None
        self._sorted_distances = None

    def compute_all_distances(self) -> None:
        """
        Compute all distances.
        """
        if not self._apsp is not None:
            self._apsp = dict(
                nx.all_pairs_dijkstra_path_length(self._graph, weight="weight")
            )
            guards = list(range(self._graph.number_of_nodes()))
            self._sorted_distances = [
                ((i, j), self._apsp[i][j]) for i, j in itertools.combinations(guards, 2)
            ]
            self._sorted_distances.sort(key=lambda x: x[1])

    def get_next_higher_distance(self, d: float) -> float:
        """
        Get the next higher distance.
        """
        self.compute_all_distances()
        assert self._sorted_distances is not None
        for (_i, _j), dist in self._sorted_distances:
            if dist > d:
                return dist
        return math.inf

    def get_next_lower_distance(self, d: float) -> float:
        """
        Get the next lower distance.
        """
        self.compute_all_distances()
        assert self._sorted_distances is not None
        for (_i, _j), dist in reversed(self._sorted_distances):
            if dist < d:
                return dist
        return 0.0

    def min_distance_of_guards(self, guards: typing.List[int]) -> float:
        """
        Compute the minimum distance of the given guards.
        """
        self.compute_all_distances()
        assert self._apsp is not None
        if not guards:
            msg = "Empty list of guards."
            raise ValueError(msg)
        if len(guards) == 1:
            return math.inf
        return min(self._apsp[i][j] for i, j in itertools.combinations(guards, 2))

    def distance(self, i: int, j: int) -> float:
        if self._apsp:
            return self._apsp[i][j]
        return nx.shortest_path_length(self._graph, i, j, weight="weight")

    def shortest_path(self, i: int, j: int) -> typing.List[int]:
        sp = nx.shortest_path(self._graph, i, j, weight="weight")
        assert isinstance(sp, list)
        return sp
