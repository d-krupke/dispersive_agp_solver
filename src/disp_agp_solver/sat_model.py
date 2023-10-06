import typing
from pysat.solvers import Solver
from threading import Timer
from .instance import Instance

class SatModel:
    def __init__(self, instance: Instance, solver: str="Glucose4") -> None:
        self._instance = instance
        self._sat_solver = Solver(name=solver, incr=True)
        self._sat_solver.add_clause(i + 1 for i in range(instance.num_positions()))
        self._model = None

    def add_coverage_constraint(self, vertices: typing.List[int]):
        #print("add_coverage_constraint:", vertices)
        self._sat_solver.add_clause([i + 1 for i in vertices])

    def prohibit_guard_pair(self, guard_a: int, guard_b: int):
        """
        Prevent that these two guards are selected together.
        """
        #print("add_distance_constraint:", guard_a, guard_b)
        self._sat_solver.add_clause([-(guard_a + 1), -(guard_b + 1)])

    def solve(self, timelimit: float=900) -> bool:
        """
        Return a list of indices of guards that should be selected.
        """
        if timelimit <= 0:
            raise ValueError("timelimit must be positive")
        def interrupt(solver):
            print("Timeout for SAT-call reached.")
            solver.interrupt()
        timer = Timer(timelimit, interrupt, [self._sat_solver])
        timer.start()
        status = self._sat_solver.solve_limited(expect_interrupt=True)
        timer.cancel()
        if status is None:
            raise TimeoutError("SAT solver timed out")
        if not status:
            # infeasible
            return False
        self._model = self._sat_solver.get_model()
        #print("Solved:", self._model)
        assert self._model is not None
        return True

    def get_solution(self) -> typing.List[int]:
        if self._model is None:
            raise RuntimeError("No solution available")
        return [i - 1 for i in self._model if i > 0]

    def __del__(self):
        self._sat_solver.delete()