!!! info "About implemented models"

    In principle, every model can be implemented in `spectrafit` by extending
    the module `spectrafit.models` by a new functions. It is important to know
    that the `raise` check have to be extend by the new function name in the
    `solver_model` and `calculated_model`.

    ```python
    __implemented_models__ = [
        "gaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
        "exponential",
        "power",
        "linear",
        "constant",
        "erf",
        "atan",
        "log",
        "heaviside",
        "my_new_model",
    ]
    ...
    for model in params:
        model = model.lower()
        if model.split("_")[0] not in __implemented_models__:
            raise KeyError(f"{model} is not supported")
        peak_kwargs[(model.split("_")[-1], model.split("_")[0])][
            model.split("_")[1]
        ] = params[model]

    for key, _kwarg in peak_kwargs.items():
        if key[1] == "my_new_model":
            val += my_new_model(x, **_kwarg)
        ...


    def my_new_model(
        x: np.array, amplitude: float = 1.0, center: float = 0.0, fwhmg: float = 1.0
    ) -> np.array:
        r"""Return a 1-dimensional `m`y_new_model` distribution."""


    ...
    ```
    Further information about implemented own models in `lmfit` can be found
    in this [example][1]. So far, the built-in models of lmfit are not
    supported, yet.

!!! warning "Change in notation for the Full Maximum Half Widht (FWHM)"

    The notation for the Full Maximum Half Widht (FWHM) is adapted due to
    changes in the `**kwargs`-handling in the models; see also
    [API](../../api/modelling_api/) and [CHANGELOG](../../changelog).
    The notation becomes:

    | Method              | _Old_ Notation | _New_ Notation |
    | ------------------- | -------------- | -------------- |
    | **Gaussian-FWHM**   | `fwhm`         | `fwhmg`        |
    | **Lorentzian-FWHM** | `fwhm`         | `fwhml`        |
    | **Pseudo-Voigt**    | `fwhm_g`       | `fwhmg`        |
    | **Pseudo-Voigt**    | `fwhm_l`       | `fwhml`        |
    | **Voigt**           | `fwhm`         | `fwhmv`        |

## Implemented models

Here is a list of implemented models of `spectrafit`:

::: spectrafit.models.gaussian

::: spectrafit.models.lorentzian

::: spectrafit.models.pseudovoigt

::: spectrafit.models.voigt

::: spectrafit.models.exponential

::: spectrafit.models.power

::: spectrafit.models.linear

::: spectrafit.models.constant

::: spectrafit.models.step

## Important constans for the models

For calculating the models a few math constants are needed, which are
implemented in the `constants` module.

::: spectrafit.models.Constants

[1]
https://lmfit.github.io/lmfit-py/examples/documentation/model_two_components.html#sphx-glr-examples-documentation-model-two-components-py
