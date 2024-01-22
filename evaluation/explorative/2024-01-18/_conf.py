"""
Having a separate file for the configuration of paths and constants allows
you to, e.g., quickly change the database without having to overwrite the
old data.
"""
from pathlib import Path

from disp_agp_solver import SearchStrategy

TIME_LIMIT = 90

PARAMS_TO_COMPARE = [
    {
        "backend": "SAT",
        "search_strategy_start": SearchStrategy.BINARY,
        "search_strategy_iteration": SearchStrategy.BINARY,
        "lazy": True,
        "add_all_vertices_as_witnesses": True,
    },
    {
        "backend": "SAT",
        "search_strategy_start": SearchStrategy.BINARY,
        "search_strategy_iteration": SearchStrategy.BINARY,
        "lazy": False,
        "add_all_vertices_as_witnesses": True,
    },
    {
        "backend": "SAT",
        "search_strategy_start": SearchStrategy.UP,
        "search_strategy_iteration": SearchStrategy.UP,
        "lazy": True,
        "add_all_vertices_as_witnesses": True,
    },
        {
        "backend": "SAT",
        "search_strategy_start": SearchStrategy.DOWN,
        "search_strategy_iteration": SearchStrategy.DOWN,
        "lazy": True,
        "add_all_vertices_as_witnesses": True,
    },
#        {
#        "backend": "MIP",
#
#    },
        {
        "backend": "CP-SAT",
    }
]

MIN_SIZE = 10
MAX_SIZE = 2_000
OPTIMALITY_TOLERANCES = [0.0001, 0.001, 0.01, 0.1]
# Bad instances that should be skipped
# An instance is bad if the integralization does not work and leads to self-intersections.
# It has nothing to do with the solvers themselves.
BLACKLIST = [
        "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000100_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000090_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000300_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_3.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_2.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000500_2.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/real-world/images/Salzburg/Residenzplatz-1626.graphml.xz",
]

# Data that is meant to be shared to verify the results.
PUBLIC_DATA = Path(__file__).parent / "PUBLIC_DATA"
# Data meant for debugging and investigation, not to be shared because of its size.
PRIVATE_DATA = Path(__file__).parent / "PRIVATE_DATA"

# Saving the full experiment data for potential debugging.
EXPERIMENT_DATA = PRIVATE_DATA / "full_experiment_data"
# Saving the simplified experiment data for analysis.
SIMPLIFIED_RESULTS = PUBLIC_DATA / "simplified_results.json.zip"