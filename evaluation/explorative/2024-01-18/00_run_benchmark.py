"""
This file runs the actual benchmark on the instances.

Slurminade: This script uses the slurminade package to distribute the benchmark on a cluster. If you do not have a slurm-cluster, it will run the benchmark locally.
AlgBench: This script uses the AlgBench package to capture and manage the results
"""


import logging
import slurminade  # pip install slurminade
from disp_agp_solver import SalzburgPolygonDataBase
# for saving the results easily
from algbench import Benchmark  # pip install algbench

from _conf import EXPERIMENT_DATA, TIME_LIMIT, PARAMS_TO_COMPARE, BLACKLIST, OPTIMALITY_TOLERANCES, MIN_SIZE, MAX_SIZE
from disp_agp_solver import solve, SearchStrategy

instances = SalzburgPolygonDataBase()
benchmark = Benchmark(EXPERIMENT_DATA)

# -----------------------------------------
# Distribution configuration for Slurm
# If you don't have Slurm, this won't do anything.
# If you have slurm, you have to update the configuration to your needs.
slurminade.update_default_configuration(
    # This setup is for the TU BS Alg cluster.
    # This doubles as documentation for on which cluster the benchmark was run.
    partition="alg",
    constraint="alggen05",
    mail_user="krupke@ibr.cs.tu-bs.de",
    exclusive=True,  # Only run one job per node.
    mail_type="FAIL",  # Send a mail if a job fails.
)
slurminade.set_dispatch_limit(1_000)
# -----------------------------------------



@slurminade.slurmify()  # makes the function distributable on a cluster
def load_instance_and_run_solver(instance_name, time_limit):
    instance = instances[instance_name]

    # The logging framework is much more powerful than print statements.
    # I recommend using it instead of print statements to report progress.
    logger = logging.getLogger("Evaluation")
    benchmark.capture_logger("Evaluation", logging.INFO)

    def run_solver(instance_name, params, opt_tol, time_limit, _instance):
        # Arguments starting with _ are not saved in the experiment data.
        # The instance is already in the instance database.
        # We only need the instance name to compare the results.

        sol, obj, ub = solve(_instance, logger=logger, opt_tol=opt_tol, time_limit=time_limit, **params)
        return {
            "solution": sol,
            "upper_bound": ub,
            "objective": obj,
        }

    # Will only run if the instance is not already solved.
    for params in PARAMS_TO_COMPARE:
        for opt_tol in OPTIMALITY_TOLERANCES:
            benchmark.add(
                run_solver, instance_name, params, opt_tol, time_limit, instance)
            

# --------------------------
# Compression is not thread-safe so we make it a separate function
# if you only notify about failures, you may want to do
# ``@slurminade.slurmify(mail_type="ALL)`` to be notified after completion.
@slurminade.slurmify()
def compress():
    benchmark.compress()

# --------------------------
# Run the benchmark on all instances.
if __name__ == "__main__":
    # Distribute the benchmark on a cluster.
    with slurminade.Batch(max_size=5) as batch:
        for instance_name in instances.iter_range(MIN_SIZE, MAX_SIZE):
            if instance_name in BLACKLIST:
                continue
            load_instance_and_run_solver.distribute(instance_name, time_limit = TIME_LIMIT)
        # compress the results at the end.
        job_ids = batch.flush()
        compress.wait_for(job_ids).distribute()