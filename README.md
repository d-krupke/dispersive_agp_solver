# Dispersive AGP Solver

_2023-10-03 Dominik Krupke_

This folder contains an exact solver for the Dispersive AGP (with vertex
guards). It has been developed on inquiry of Christian Rieck to make the results
viable for the CG:SHOP grant. It uses an iterative SAT-model and lazy
constraints for coverage via witnesses to solve the problem. The minimal
distance is incrementally increased until the formula becomes infeasible, which
indicates that the previous distance was the optimal one.

The code is written in Python with C++-bindings for CGAL. However, the CGAL-part
was outsourced to an auxiliary library. The CGAL-part may have some license
implications for commercial use (unlikely).

![example](https://github.com/d-krupke/dispersive_agp_solver/blob/main/docs/figures/animation.gif?raw=true)

## Installation

The code is properly packaged and can be installed via pip. This allows you to
easily play around with the code and convince yourself that it works, without
having to deal with complex compilation issues or dependencies.

TODO: The visibility package is not public yet.

## Algorithm

The algorithm is based on the following SAT-formula:

- Create a boolean variable for each vertex representing placing a guard at this
  position.
- Enforce that one of the guards has to be used (simple OR-clause over all
  variables).

Now we repeatedly do the following:

- Solve the SAT-formula.
- If the formula is infeasible, we have restricted the sparsification too much.
  Return last feasible solution.
- Compute the missing area (i.e., the area that is not covered by the selected
  guards).
- If the missing area is empty, we have a new feasible solution. To improve it
  further, we find the closest two used guards and prohibit them to be used at
  the same time. This is a simple OR-clause.
- If the missing area is not empty, we find witnesses for the missing area and
  enforce at least of guard within the visibility range of each witness. This is
  again a simple OR-clause.
