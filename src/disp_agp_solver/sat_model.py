import typing
from threading import Timer

from pysat.solvers import Solver

from .instance import Instance


class SatModel:
    def __init__(self, instance: Instance, solver: str = "Glucose4") -> None:
        self._instance = instance
        self._sat_solver = Solver(name=solver, incr=True)
        self._sat_solver.add_clause(i + 1 for i in range(instance.num_positions()))
        self._model = None

    def add_coverage_constraint(self, vertices: typing.List[int]):
        # print("add_coverage_constraint:", vertices)
        assert all(0 <= i < self._instance.num_positions() for i in vertices)
        assert len(vertices) > 0
        self._sat_solver.add_clause([i + 1 for i in vertices])

    def prohibit_guard_pair(self, guard_a: int, guard_b: int):
        """
        Prevent that these two guards are selected together.
        """
        # print("add_distance_constraint:", guard_a, guard_b)
        assert 0 <= guard_a < self._instance.num_positions()
        assert 0 <= guard_b < self._instance.num_positions()
        assert guard_a != guard_b
        self._sat_solver.add_clause([-(guard_a + 1), -(guard_b + 1)])

    def solve(self, timelimit: float = 900) -> bool:
        """
        Return a list of indices of guards that should be selected.
        """
        if timelimit <= 0:
            msg = "timelimit must be positive"
            raise ValueError(msg)

        def interrupt(solver):
            solver.interrupt()

        timer = Timer(timelimit, interrupt, [self._sat_solver])
        timer.start()
        status = self._sat_solver.solve_limited(expect_interrupt=True)
        timer.cancel()
        if status is None:
            msg = "SAT solver timed out"
            raise TimeoutError(msg)
        if not status:
            # infeasible
            return False
        self._model = self._sat_solver.get_model()
        # print("Solved:", self._model)
        assert self._model is not None
        return True

    def get_solution(self) -> typing.List[int]:
        if self._model is None:
            msg = "No solution available"
            raise RuntimeError(msg)
        return [i - 1 for i in self._model if i > 0]

    def __del__(self):
        self._sat_solver.delete()
