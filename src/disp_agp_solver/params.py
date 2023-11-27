from .distance_optimizer import SearchStrategy

class OptimizerParams:
    def __init__(
        self,
        search_strategy_start: SearchStrategy = SearchStrategy.BINARY,
        search_strategy_iteration: SearchStrategy = SearchStrategy.BINARY,
        lazy: bool = True,
        add_all_vertices_as_witnesses: bool = True,
    ) -> None:
        self.search_strategy_start = search_strategy_start
        self.search_strategy_iteration = search_strategy_iteration
        self.lazy = lazy
        self.add_all_vertices_as_witnesses = add_all_vertices_as_witnesses