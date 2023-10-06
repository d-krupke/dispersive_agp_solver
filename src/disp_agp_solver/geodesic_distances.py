"""
This code computes the geodesic distances between all pairs of positions in an instance.
It is based on the visibility polygon calculator from the pyvispoly package.
It is a well known result that the geodesic distance between two points in a polygon
can be computed purely by connecting all vertices that can view each other and then
computing the shortest path between the two points in the resulting graph.
"""

from pyvispoly import Point, Polygon, PolygonWithHoles, VisibilityPolygonCalculator
import networkx as nx
import math
import typing

from .instance import Instance

class GeodesicDistances:
    def __init__(self, instance: Instance) -> None:
        poly = instance.as_cgal_polygon()
        self._visibility_polygon_calculator = VisibilityPolygonCalculator(poly)
        self._vis_polys = [self._visibility_polygon_calculator.compute_visibility_polygon(instance.as_cgal_position(i))
                            for i in range(instance.num_positions())]
        self._graph = nx.Graph()
        self._graph.add_nodes_from(range(instance.num_positions()))
        for i in range(instance.num_positions()):
            for j in range(i+1, instance.num_positions()):
                if self._vis_polys[i].contains(instance.as_cgal_position(j)):
                    dist = math.sqrt((instance.positions[i][0]-instance.positions[j][0])**2 
                                     + (instance.positions[i][1]-instance.positions[j][1])**2)
                    self._graph.add_edge(i, j, weight = dist)
        if not nx.is_connected(self._graph):
            raise ValueError("Instance is not connected")
        
    def distance(self, i: int, j: int) -> float:
        return nx.shortest_path_length(self._graph, i, j, weight="weight")
    
    def shortest_path(self, i: int, j: int) -> typing.List[int]:
        sp = nx.shortest_path(self._graph, i, j, weight="weight")
        assert isinstance(sp, list)
        return sp
        