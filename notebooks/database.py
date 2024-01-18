# %%
from disp_agp_solver import SalzburgPolygonDataBase

db = SalzburgPolygonDataBase()
import faulthandler

# %%
list(db.iter_range(0, 100))

# %%
import logging

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DispAGP")
logger.setLevel(logging.INFO)

# time stamps
if not logger.hasHandlers():
    logging_handler = logging.StreamHandler()
    logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(logging_handler)

logger.info("Test")
faulthandler.enable()
from disp_agp_solver import solve

bad_urls = [
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000100_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000090_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000300_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_3.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_2.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-a-2opt/spg-a-poly_0000300_1.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/random/spg-c-alg6/spg-c-poly_0000500_2.graphml.xz",
    "https://sbgdb.cs.sbg.ac.at/db/sbgdb-20200507/polygons/real-world/images/Salzburg/Residenzplatz-1626.graphml.xz",
]
for instance_url in db.iter_range(800, 2000):
    if instance_url in bad_urls:
        continue
    print(instance_url)
    instance = db[instance_url]
    solution, obj, ub = solve(instance, logger=logger, time_limit=60)
    print(solution)

