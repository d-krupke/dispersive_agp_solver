# Dispersive AGP Solver

_2023-10-03 Dominik Krupke_

This folder contains an exact solver for the Dispersive AGP (with vertex
guards). It has been developed on inquiry of Christian Rieck to make the results
viable for the CG:SHOP grant. It uses an iterative SAT-model and lazy
constraints for coverage via witnesses to solve the problem. The minimal
distance is incrementally increased until the formula becomes infeasible, which
indicates that the previous distance was the optimal one.

![example](https://github.com/d-krupke/dispersive_agp_solver/blob/main/docs/figures/animation.gif?raw=true)

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

**Input**: A polygon \( P \)  
**Output**: A set of guards ensuring maximum dispersion  

1: Initialize \( \text{vertices} = P.\text{vertices} \)  
2: Initialize \( \text{SATFormula} \) as an empty SAT instance  
3: For \( v \) in \( \text{vertices} \):  
&nbsp;&nbsp;&nbsp;&nbsp;Introduce a new Boolean variable \( x_v \) into \( \text{SATFormula} \) representing the placement of a guard at vertex \( v \)  

4: Add a clause to \( \text{SATFormula} \) to enforce at least one guard:  
&nbsp;&nbsp;&nbsp;&nbsp;\[ \bigvee_{v \in \text{vertices}} x_v \]  

5: **while** True:  
&nbsp;&nbsp;&nbsp;&nbsp;5.1: \( \text{solution} \) = Solve(\( \text{SATFormula} \))  
&nbsp;&nbsp;&nbsp;&nbsp;5.2: **if not** \( \text{solution} \):  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Return \( \text{LastFeasibleSolution} \)  
&nbsp;&nbsp;&nbsp;&nbsp;5.3: \( \text{guards} \) = { \( v \) | \( v \) in \( \text{vertices} \) and \( \text{solution}(x_v) \) is True }  
&nbsp;&nbsp;&nbsp;&nbsp;5.4: \( \text{missingArea} \) = ComputeMissingArea(\( P, \text{guards} \))  
&nbsp;&nbsp;&nbsp;&nbsp;5.5: **if** \( \text{missingArea} \) is empty:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.5.1: \( \text{LastFeasibleSolution} \) = \( \text{guards} \)  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.5.2: \( g_1, g_2 \) = FindClosestGuardsPair(\( \text{guards} \))  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.5.3: Add a new clause to \( \text{SATFormula} \) to prevent \( g_1 \) and \( g_2 \) from being chosen simultaneously:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\[ \neg x_{g_1} \vee \neg x_{g_2} \]  
&nbsp;&nbsp;&nbsp;&nbsp;5.6: **else**:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.6.1: For \( \text{witness} \) in FindWitnessesForMissingArea(\( \text{missingArea} \)):  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.6.1.1: \( \text{visibleGuards} \) = FindVisibleGuards(\( \text{witness}, \text{guards} \))  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5.6.1.2: Add a new clause to \( \text{SATFormula} \):  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\[ \bigvee_{g \in \text{visibleGuards}} x_g \]  

**End**



## License

While this code is licensed under the MIT license, it has a dependency on [CGAL](https://www.cgal.org/),
which is licensed under GPL. This may have some implications for commercial use.