# Dispersive AGP Solver

_2023-10-03 Dominik Krupke_

This folder contains an exact solver for the Dispersive AGP (with vertex
guards). It has been developed on inquiry of Christian Rieck to make the results
viable for the CG:SHOP grant. It uses an iterative SAT-model and lazy
constraints for coverage via witnesses to solve the problem. The minimal
distance is incrementally increased until the formula becomes infeasible, which
indicates that the previous distance was the optimal one.

![example](https://github.com/d-krupke/dispersive_agp_solver/blob/main/docs/figures/animation.gif?raw=true)

![complex example](https://github.com/d-krupke/dispersive_agp_solver/blob/main/docs/figures/example_more_complex.gif?raw=true)

## Problem Description


**Optimization Dispersive Art Gallery Problem (Vertex Guarding)**

**Input:**
1. A polygon \( P \) with vertices \( V(P) \).

**Objective:** 
Determine the maximum distance \( \ell^* \) such that there exists a set of guards, \( G \), positioned on the vertices of the polygon \( P \) (i.e., \( G \subseteq V(P) \)) with the following properties:

1. Every point inside \( P \) is visible to at least one guard in \( G \).
2. The pairwise geodesic distances between any two guards in \( G \) are at least \( \ell^* \).

---

Note: The visibility between a point and a guard is determined by a straight line segment that does not intersect the exterior of the polygon \( P \).

This problem was introduced by [Rieck and Scheffer](https://arxiv.org/pdf/2209.10291.pdf).

## Installation

You can easily install and use the solver via pip:

```bash
pip install --verbose git+https://github.com/d-krupke/dispersive_agp_solver
```

We put some effort into making the installation as easy as possible. However,
you will need to have a modern C++-compiler installed. There may also be some
problems with Windows. The installation of the dependencies can take a while as
CGAL will be locally installed (and compiled). Depending on your system, this
can take up to 30 minutes.

You could also try to install the visibility polygon dependency
[pyvispoly](https://github.com/d-krupke/pyvispoly) before installing this
package. This dependency is probably the most difficult to install. If you
manage to install it, the installation of this package should be easy.

## Algorithm

The algorithm is based on an incremental SAT-model, in which we
* incrementally ensure full coverage of the polygon by adding witnesses for
  missing areas
* incrementally increase the minimal distance between guards until the formula
  becomes infeasible

### Algorithm 1: Dispersive Gallery Optimization

**Input**: A polygon \( P \)  
**Output**: A set of guards ensuring maximum dispersion


1. Initialize `vertices = P.vertices`
2. Initialize `SATFormula` as an empty SAT instance
3. For `v` in `vertices`:
   - Introduce a new Boolean variable $x_v$ into `SATFormula` representing the placement of a guard at vertex `v`
4. Add a clause to `SATFormula` to enforce at least one guard:  
   $\bigvee_{v \in \text{vertices}} x_v$
5. **while** True:
   1. `solution = Solve(SATFormula)`
   2. **if not** `solution`:  
      - Return `LastFeasibleSolution`
   3. `guards = { v | v in vertices and solution(x_v) is True }`
   4. `missingArea = ComputeMissingArea(P, guards)`
   5. **if** `missingArea` is empty:
      1. `LastFeasibleSolution = guards`
      2. $g_1, g_2$ = `FindClosestGuardsPair(guards)`
      3. Add a new clause to `SATFormula` to prevent $g_1$ and $g_2$ from being chosen simultaneously:  
      $\neg x_{g_1} \vee \neg x_{g_2}$
   6. **else**:
      1. For `witness` in `FindWitnessesForMissingArea(missingArea)`:
         1. `visibleGuards = FindVisibleGuards(witness, guards)`
         2. Add a new clause to `SATFormula`: $\bigvee_{g \in \text{visibleGuards}} x_g$


## Potential Improvements

Most of the time is used by the geometric operations, while the SAT-formulas remain harmless.
Thus, one could try another approach by always computing an optimal solution for each witness set and
only then start to extend it. This would drastically reduce the number of geometric operations.
A lot of the data can be reused. Would require some changes in the code architecture.

Alternative approaches could be based on a MIP or CP-SAT model.
They would probably not be competitive.
However, they could minimize the number of guards in parallel and, thus, potentially make larger optimization steps.

## License

While this code is licensed under the MIT license, it has a dependency on [CGAL](https://www.cgal.org/),
which is licensed under GPL. This may have some implications for commercial use.
