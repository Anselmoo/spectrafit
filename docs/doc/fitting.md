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

[1]:
  https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimizer#lmfit.minimizer.Minimizer
[2]: https://lmfit.github.io/lmfit-py/fitting.html?highlight=minimize
