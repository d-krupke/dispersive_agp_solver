import typing
from threading import Timer
import logging
from pysat.solvers import Solver

from .instance import Instance


class BasicSatModel:
    def __init__(self, instance: Instance, solver: str = "Glucose4", logger: typing.Optional[logging.Logger]=None) -> None:
        if logger is None:
            self._logger = logging.getLogger("DispAgpSatModel")
        else:
            self._logger = logger
        self._instance = instance
        self._sat_solver = Solver(name=solver, incr=True)
        self._sat_solver.add_clause(i + 1 for i in range(instance.num_positions()))
        self._model = None
        self._num_coverage_constraints = 0
        self._num_prohibited_guards = 0

    def add_coverage_constraint(self, vertices: typing.List[int]):
        assert all(0 <= i < self._instance.num_positions() for i in vertices)
        assert len(vertices) > 0
        self._sat_solver.add_clause([i + 1 for i in vertices])
        self._num_coverage_constraints += 1
        self._logger.debug("Added coverage constraint for %d vertices.", len(vertices))

    def prohibit_guard_pair(self, guard_a: int, guard_b: int):
        """
        Prevent that these two guards are selected together.
        """
        assert 0 <= guard_a < self._instance.num_positions()
        assert 0 <= guard_b < self._instance.num_positions()
        assert guard_a != guard_b
        self._sat_solver.add_clause([-(guard_a + 1), -(guard_b + 1)])
        self._num_prohibited_guards += 1
        self._logger.debug("Prohibited guard pair (%d, %d).", guard_a, guard_b)

    def solve(self, timelimit: float = 900) -> bool:
        """
        Return a list of indices of guards that should be selected.
        """
        if self._num_coverage_constraints == 0:
            raise RuntimeError("No coverage constraints added.")
        self._logger.info("Solving SAT-formula with timelimit %f.", timelimit)
        if timelimit <= 0:
            msg = "timelimit must be positive"
            raise ValueError(msg)

        def interrupt(solver):
            solver.interrupt()

        timer = Timer(timelimit, interrupt, [self._sat_solver])
        timer.start()
        status = self._sat_solver.solve_limited(expect_interrupt=True)
        self._logger.info("SAT solver terminated (%fs).", self._sat_solver.time())
        timer.cancel()
        if status is None:
            self._logger.info("SAT solver timed out.")
            msg = "SAT solver timed out"
            raise TimeoutError(msg)
        if not status:
            # infeasible
            self._logger.info("SAT-formula is unsatisfiable.")
            return False
        self._model = self._sat_solver.get_model()
        self._logger.info("SAT-formula is satisfiable.")
        assert self._model is not None
        return True

    def get_solution(self) -> typing.List[int]:
        if self._model is None:
            msg = "No solution available"
            raise RuntimeError(msg)
        return [i - 1 for i in self._model if i > 0]
    
    def get_statistics(self):
        stats =  self._sat_solver.accum_stats().copy()
        stats.update({
            "num_coverage_constraints": self._num_coverage_constraints,
            "num_prohibited_guards": self._num_prohibited_guards,
        })
        return stats

    def __del__(self):
        self._sat_solver.delete()
