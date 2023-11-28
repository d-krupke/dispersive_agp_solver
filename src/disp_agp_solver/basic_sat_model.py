import logging
import typing
from threading import Timer

from pysat.solvers import Solver

from .instance import Instance
from .timer import Timer as StopWatch


class BasicSatModel:
    def __init__(
        self,
        instance: Instance,
        solver: str = "Glucose4",
        logger: typing.Optional[logging.Logger] = None,
    ) -> None:
        if logger is None:
            self._logger = logging.getLogger("DispAgpSatModel")
        else:
            self._logger = logger
        self._solver_name = solver
        self._instance = instance
        self._sat_solver = Solver(name=solver, incr=True)
        self._sat_solver.add_clause(i + 1 for i in range(instance.num_positions()))
        self._model = None
        self._num_coverage_constraints = 0
        self._num_prohibited_guards = 0
        self._stats = {
            "solve_calls": 0,
            "num_resets": 0,
            "solve_statistics": [],
        }

    def reset_constraints(self):
        self._stats["num_resets"] += 1
        self._sat_solver.delete()
        self._sat_solver = Solver(name=self._solver_name, incr=True)
        self._sat_solver.add_clause(
            i + 1 for i in range(self._instance.num_positions())
        )
        self._num_coverage_constraints = 0
        self._num_prohibited_guards = 0
        self._model = None

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

    def _log_solver_stats(self, status, time):
        self._stats["solve_calls"] += 1
        self._stats["solve_statistics"].append(
            {
                "status": status,
                "time": time,
                "num_coverage_constraints": self._num_coverage_constraints,
                "num_prohibited_guards": self._num_prohibited_guards,
            }
        )
        self._stats["solve_statistics"][-1].update(self._sat_solver.accum_stats())

    def solve(self, timelimit: float = 900) -> bool:
        """
        Return a list of indices of guards that should be selected.
        """
        if self._num_coverage_constraints == 0:
            msg = "No coverage constraints added."
            raise RuntimeError(msg)
        self._logger.info("Solving SAT-formula with timelimit %f.", timelimit)
        if timelimit <= 0:
            msg = "timelimit must be positive"
            raise ValueError(msg)

        def interrupt(solver):
            solver.interrupt()

        timer = Timer(timelimit, interrupt, [self._sat_solver])
        stop_watch = StopWatch()
        timer.start()
        status = self._sat_solver.solve_limited(expect_interrupt=True)
        self._log_solver_stats(status, stop_watch.time())
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

    def get_stats(self):
        return self._stats.copy()

    def __del__(self):
        self._sat_solver.delete()
