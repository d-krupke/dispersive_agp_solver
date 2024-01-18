import typing

from .distance_optimizer import SearchStrategy


class OptimizerParams:
    def __init__(
        self,
        search_strategy_start: typing.Union[
            SearchStrategy, str
        ] = SearchStrategy.BINARY,
        search_strategy_iteration: typing.Union[
            SearchStrategy, str
        ] = SearchStrategy.BINARY,
        lazy: bool = True,
        add_all_vertices_as_witnesses: bool = True,
    ) -> None:
        if isinstance(search_strategy_start, str):
            search_strategy_start = SearchStrategy[search_strategy_start]
        if isinstance(search_strategy_iteration, str):
            search_strategy_iteration = SearchStrategy[search_strategy_iteration]
        self.search_strategy_start = search_strategy_start
        self.search_strategy_iteration = search_strategy_iteration
        self.lazy = lazy
        self.add_all_vertices_as_witnesses = add_all_vertices_as_witnesses
