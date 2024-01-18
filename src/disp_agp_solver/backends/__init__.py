from .sat import OptimizerParams, SatBasedOptimizer
from .cp import CpSatOptimizer
from .mip import GurobiOptimizer

def solve(
    instance,
    backend: str = "SAT",
    time_limit=900.0,
    opt_tol=0.0001,
    logger=None,
    **params,
):
    if backend == "SAT":
        solver = SatBasedOptimizer(
            instance, logger=logger, params=OptimizerParams(**params)
        )
        solver.solve(time_limit, opt_tol)
        return solver.solution, solver.objective, solver.upper_bound
    elif backend == "CP-SAT":
        solver = CpSatOptimizer(instance, logger=logger)
        solver.solve(time_limit, opt_tol)
        return solver.solution, solver.objective, solver.upper_bound
    elif backend == "MIP":
        solver = GurobiOptimizer(instance, logger=logger)
        solver.solve(time_limit, opt_tol)
        return solver.solution, solver.objective, solver.upper_bound
    msg = f"Invalid backend: {backend}"
    raise NotImplementedError(msg)


__all__ = ["SatBasedOptimizer", "OptimizerParams", "solve"]
