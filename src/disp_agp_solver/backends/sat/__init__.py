import logging
import typing

from disp_agp_solver.instance import Instance

from .optimizer import SatBasedOptimizer
from .params import OptimizerParams, SearchStrategy


def solve(
    instance: Instance,
    time_limit: float = 900.0,
    opt_tol: float = 0.0001,
    logger: typing.Optional[logging.Logger] = None,
    **params,
) -> typing.Tuple[typing.List[int], float, float]:
    solver = SatBasedOptimizer(
        instance, logger=logger, params=OptimizerParams(**params)
    )
    solver.solve(time_limit, opt_tol)
    return solver.solution, solver.objective, solver.upper_bound


__all__ = ["SatBasedOptimizer", "OptimizerParams", "SearchStrategy", "solve"]
