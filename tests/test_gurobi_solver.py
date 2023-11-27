from disp_agp_solver import Instance, GurobiSolver
from pyvispoly import PolygonWithHoles, Point
import math

def test_square():
    instance = Instance([(0, 0), (1, 0), (1, 1), (0, 1)], [0,1,2,3])
    optimizer = GurobiSolver(instance)
    status = optimizer.solve(10)
    assert status == GurobiSolver.Status.OPTIMAL
    assert optimizer.objective == math.inf
    assert len(optimizer.solution) == 1

def test_square_with_hole():
    instance = Instance([(0,0), (10, 0), (10, 10), (0, 10), (4,4), (6,4), (6,6), (4,6)], [0,1,2,3], [[4,5,6,7]])
    optimizer = GurobiSolver(instance)
    status = optimizer.solve(10)
    assert status == GurobiSolver.Status.OPTIMAL
    assert optimizer.objective < 20.0
    assert optimizer.objective > 10.0
    assert len(optimizer.solution) >= 2