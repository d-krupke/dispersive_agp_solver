"""
This code computes the geodesic distances between all pairs of positions in an instance.
It is based on the visibility polygon calculator from the pyvispoly package.
It is a well known result that the geodesic distance between two points in a polygon
can be computed purely by connecting all vertices that can view each other and then
computing the shortest path between the two points in the resulting graph.
"""

import math
import typing

import networkx as nx

from .instance import Instance
from .guard_coverage import GuardCoverage

class GeodesicDistances:
    def __init__(self, instance: Instance, guard_coverage: typing.Optional[GuardCoverage]) -> None:
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
        
    def compute_all_distances(self) -> None:
        """
        Compute all distances.
        """
        if not self._apsp is not None:
            self._apsp = dict(nx.all_pairs_dijkstra_path_length(self._graph, weight="weight"))
    

    def distance(self, i: int, j: int) -> float:
        if self._apsp:
            return self._apsp[i][j]
        return nx.shortest_path_length(self._graph, i, j, weight="weight")

    def shortest_path(self, i: int, j: int) -> typing.List[int]:
        sp = nx.shortest_path(self._graph, i, j, weight="weight")
        assert isinstance(sp, list)
        return sp
