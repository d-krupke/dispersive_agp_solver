from .instance import Instance
import matplotlib.pyplot as plt
from pyvispoly import plot_polygon
from .guard_coverage import GuardCoverage
class Plotter:
    def __init__(self, instance: Instance):
        self.instance = instance
        self._guard_coverage = GuardCoverage(instance)

    def plot_instance(self, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        plot_polygon(self.instance.as_cgal_polygon(), color="lightblue", ax=ax)
        ax.set_aspect("equal")
        return ax
    
    def plot_witnesses(self, witnesses, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        for witness, covering_guards in witnesses:
            for covering_guard in covering_guards:
                ax.plot(
                    [self.instance.positions[covering_guard][0], float(witness.x())],
                    [self.instance.positions[covering_guard][1], float(witness.y())],
                    "r--",
                    lw=0.5,
                )
            ax.plot([float(witness.x())], [float(witness.y())], "x", color="darkred")
        return ax
    
    def plot_guards(self, guards, highlighted_guards= None, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        highlighted_guards = highlighted_guards if highlighted_guards else []
        for guard in guards:
            if guard in highlighted_guards:
                ax.plot(
                    self.instance.positions[guard][0],
                    self.instance.positions[guard][1],
                    "o",
                    color="red",
                )
            else:
                ax.plot(
                    self.instance.positions[guard][0],
                    self.instance.positions[guard][1],
                    "o",
                    color="darkgreen",
                )
        return ax
    
    def plot_solution_with_coverage(self, guards, witness_positions, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        self.plot_instance(ax)
        uncovered_areas = self._guard_coverage.compute_uncovered_area(guards)
        for area in uncovered_areas:
            plot_polygon(area, color="red", ax=ax, alpha=0.3)
        self.plot_guards(guards, None, ax=ax)
        ax.plot([w.x() for w in witness_positions], [w.y() for w in witness_positions], "x", color="grey")
        return ax
    
    def plot_solution_with_coverage_and_new_witnesses(self, guards, witness_positions, new_witnesses, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        self.plot_instance(ax)
        uncovered_areas = self._guard_coverage.compute_uncovered_area(guards)
        for area in uncovered_areas:
            plot_polygon(area, color="red", ax=ax, alpha=0.3)
        self.plot_guards(guards, None, ax=ax)
        ax.plot([w.x() for w in witness_positions], [w.y() for w in witness_positions], "x", color="grey")
        self.plot_witnesses(new_witnesses, ax=ax)
        return ax

    def plot_solution(self, guards, witness_positions, ax=None):
        if ax is None:
            fig, ax = plt.subplots()
        self.plot_instance(ax)
        self.plot_guards(guards, None, ax=ax)
        ax.plot([w.x() for w in witness_positions], [w.y() for w in witness_positions], "x", color="grey")

