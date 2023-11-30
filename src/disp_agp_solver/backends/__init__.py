from .sat import SatBasedOptimizer, OptimizerParams
from .mip import GurobiOptimizer
from .cp import CpSatOptimizer

def solve(instance, backend:str = "SAT", time_limit=900.0, opt_tol=0.0001, logger=None, **params):
    if backend == "SAT":
        solver = SatBasedOptimizer(instance, logger=logger, params=OptimizerParams(**params))
        solver.solve(time_limit, opt_tol)
        return solver.solution, solver.objective, solver.upper_bound
    raise NotImplementedError(f"Invalid backend: {backend}")

__all__ = ["SatBasedOptimizer", "OptimizerParams", "solve"]