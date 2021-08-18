!!! info "Aboot implemented models"

    In principle, every model can be implemented in `spectrafit` by extending
    the module `spectrafit.models` by a new functions. It is important to know
    that the `raise` check have to be extend by the new function name in the
    `solver_model` and `calculated_models`.

    ```python
    val = 0.0
    for model in params:
        model = model.lower()
        if model.split("_")[0] in [
            "gaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
            "exponential",
            "powerlaw",
            "linear",
            "constant",
            "erf",
            "atan",
            "log",
            "here_comes_the_new_function",
        ]:
            pass
        else:
            raise SystemExit(f"{model} is not supported")
    for model in params:
        model = model.lower()
        if "here_comes_the_new_function" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_g" in model:
                fwhm_g = params[model]
                val += gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_g,
                )
        ...
    ```
    Further information about implemented own models in `lmfit` can be found
    in this [example](https://lmfit.github.io/lmfit-py/examples/documentation/model_two_components.html#sphx-glr-examples-documentation-model-two-components-py). So far, the
    built-in models of lmfit are not supported, yet.

## Implemented models

Here is a list of implemented models of `spectrafit`:

::: spectrafit.models.gaussian

::: spectrafit.models.lorentzian

::: spectrafit.models.pseudovoigt

::: spectrafit.models.voigt

::: spectrafit.models.exponential

::: spectrafit.models.powerlaw

::: spectrafit.models.linear

::: spectrafit.models.constant

::: spectrafit.models.step

## Important constans for the models

For calculating the models a few math constants are needed, which are
implemented in the `constants` module.

::: spectrafit.models.Constants
