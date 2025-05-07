---
title: Fitting
description: Fitting in SpectraFit
tags:
  - fitting
  - lmfit
  - scipy
  - optimization
  - solver
---

## Fitting

The fitting in `SpectraFit` is realized by `lmifit` and diveded into two parts:

1. [Minimizer][1] is the class for defining the fitting problem. The
   sub-dictionary `**args["minimizer"]` can contains all kinds of `key` and
   `value` pairs for setup the [Minimizer][1].
2. [minimizer][2] is the the function of the class [Minimizer][1] to perform the
   optimization. The sub-dictionary `**args["optimizer"]` can contains all kinds
   of `key` and `value` pairs for setup the [minimizer][2].

```python
mini = Minimizer(
    solver_model,
    params,
    fcn_args=(df[args["column"][0]].values, df[args["column"][1]].values),
    **args["minimizer"],
)
result = mini.minimize(**args["optimizer"])
```

!!! info "About \*\*kwargs"

    By making use of the \*\* operator in `python`, key-value pairs of a
    dictionary can be unpacked it into keyword arguments of a function call.

!!! tip "About implemented solvers by LMFIT"

    All the implemented solvers by LMFIT are listed in the table below:

    - [x] `leastsq`: Levenberg-Marquardt (default)
    - [x] `least_squares`: Least-Squares minimization, using Trust Region Reflective method
    - [x] `differential_evolution`: differential evolution
    - [x] `brute`: brute force method
    - [x] `basinhopping`: basinhopping
    - [x] `ampgo`: Adaptive Memory Programming for Global Optimization
    - [x] `nelder`: Nelder-Mead
    - [x] `lbfgsb`: L-BFGS-B
    - [x] `powell`: Powell
    - [x] `cg`: Conjugate-Gradient
    - [x] `newton`: Newton-CG
    - [x] `cobyla`: Cobyla
    - [x] `bfgs`: BFGS
    - [x] `tnc`: Truncated Newton
    - [x] `trust-ncg`: Newton-CG trust-region
    - [x] `trust-exact`: nearly exact trust-region
    - [x] `trust-krylov`: Newton GLTR trust-region
    - [x] `trust-constr`: trust-region for constrained optimization
    - [x] `dogleg`: Dog-leg trust-region
    - [x] `slsqp`: Sequential Linear Squares Programming
    - [x] `emcee`: Maximum likelihood via Monte-Carlo Markov Chain
    - [x] `shgo`: Simplicial Homology Global Optimization
    - [x] `dual_annealing`: Dual Annealing optimization

    Especially, the [`differential_evolution`][3] is an interesting alternative
    for solving numerically challenging fitting problems. The method based on
    this [SciPy implementation][4] is implemented in `SpectraFit` and can be
    used by setting the `minimizer` parameter to `"differential_evolution"`.

[1]: https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#lmfit.minimizer.Minimizer
[2]: https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimize
[3]: https://en.wikipedia.org/wiki/Differential_evolution
[4]: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
