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
        peak_kwargs[(model.split("_")[-1], model.split("_")[0])][model.split("_")[1]] = (
            params[model]
        )

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

::: spectrafit.models.DistributionModels.gaussian

::: spectrafit.models.DistributionModels.lorentzian

::: spectrafit.models.DistributionModels.pseudovoigt

::: spectrafit.models.DistributionModels.voigt

::: spectrafit.models.DistributionModels.exponential

::: spectrafit.models.DistributionModels.power

::: spectrafit.models.DistributionModels.linear

::: spectrafit.models.DistributionModels.constant

::: spectrafit.models.DistributionModels.erf

::: spectrafit.models.DistributionModels.heaviside

::: spectrafit.models.DistributionModels.atan

::: spectrafit.models.DistributionModels.log

::: spectrafit.models.DistributionModels.cgaussian

::: spectrafit.models.DistributionModels.clorentzian

::: spectrafit.models.DistributionModels.cvoigt

::: spectrafit.models.DistributionModels.polynom2

::: spectrafit.models.DistributionModels.polynom3

::: spectrafit.models.DistributionModels.pearson1

::: spectrafit.models.DistributionModels.pearson2

::: spectrafit.models.DistributionModels.pearson3

::: spectrafit.models.DistributionModels.pearson4

## Important constants for the models

For calculating the models a few math constants are needed, which are
implemented in the `constants` module.

::: spectrafit.models.Constants

## Visualization of the models as a function of the parameters

!!! info "About Peaks' Components"

    Comparing components of the peaks in a table is important because it allows
    for a quick and easy comparison of the different parameters that describe
    each peak. This can be useful for identifying trends or patterns in the
    data, as well as for identifying outliers or anomalies.

    Additionally, having this information in a table format can make it easier
    to visualize and interpret the data, as well as to communicate the
    results to others. This can be also seen in [example9_3.ipny][2]


    ```python
    from spectrafit.plugins import notebook as nb

    ...

    spn.solver_model(initial_model=initial_model, show_peaks=True)
    ```

    This will provide an interactive table as well as allows to export the
    iterative results as a `csv`-file.

??? Example "About Peak's Components as `*.csv`"

    ```csv
        pseudovoigt_amplitude_1,pseudovoigt_amplitude_1,pseudovoigt_amplitude_1,pseudovoigt_center_1,pseudovoigt_center_1,pseudovoigt_center_1,pseudovoigt_fwhmg_1,pseudovoigt_fwhmg_1,pseudovoigt_fwhmg_1,pseudovoigt_fwhml_1,pseudovoigt_fwhml_1,pseudovoigt_fwhml_1,gaussian_amplitude_2,gaussian_amplitude_2,gaussian_amplitude_2,gaussian_center_2,gaussian_center_2,gaussian_center_2,gaussian_fwhmg_2,gaussian_fwhmg_2,gaussian_fwhmg_2,gaussian_amplitude_3,gaussian_amplitude_3,gaussian_amplitude_3,gaussian_center_3,gaussian_center_3,gaussian_center_3,gaussian_fwhmg_3,gaussian_fwhmg_3,gaussian_fwhmg_3,gaussian_amplitude_4,gaussian_amplitude_4,gaussian_amplitude_4,gaussian_center_4,gaussian_center_4,gaussian_center_4,gaussian_fwhmg_4,gaussian_fwhmg_4,gaussian_fwhmg_4,gaussian_amplitude_5,gaussian_amplitude_5,gaussian_amplitude_5,gaussian_center_5,gaussian_center_5,gaussian_center_5,gaussian_fwhmg_5,gaussian_fwhmg_5,gaussian_fwhmg_5,gaussian_amplitude_6,gaussian_amplitude_6,gaussian_amplitude_6,gaussian_center_6,gaussian_center_6,gaussian_center_6,gaussian_fwhmg_6,gaussian_fwhmg_6,gaussian_fwhmg_6
        init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value,init_value,model_value,best_value
        1.0,0.33834723012149714,0.33834723012149714,0.0,0.017248125260695968,0.017248125260695968,0.1,0.020000000004318036,0.020000000004318036,0.1,0.1999999999970698,0.1999999999970698,0.3,0.04935454783731008,0.04935454783731008,2.0,1.6275712126681712,1.6275712126681712,0.1,0.2999853736750539,0.2999853736750539,0.3,0.08603886973285346,0.08603886973285346,2.5,2.447935058411735,2.447935058411735,0.2,0.3999999771273954,0.3999999771273954,0.3,0.07288548037982234,0.07288548037982234,2.5,2.031809677600558,2.031809677600558,0.3,0.399999999994134,0.399999999994134,0.3,0.0806454229648127,0.0806454229648127,3.0,3.0955581713143245,3.0955581713143245,0.3,0.39999999989892293,0.39999999989892293,0.3,0.09759693340603837,0.09759693340603837,3.8,3.7000000000154216,3.7000000000154216,0.3,0.39999931341337847,0.39999931341337847
        1.0,0.33834723012149714,0.33834723012149714,0.0,0.017248125260695968,0.017248125260695968,0.1,0.020000000004318036,0.020000000004318036,0.1,0.1999999999970698,0.1999999999970698,0.3,0.04935454783731008,0.04935454783731008,2.0,1.6275712126681712,1.6275712126681712,0.1,0.2999853736750539,0.2999853736750539,0.3,0.08603886973285346,0.08603886973285346,2.5,2.447935058411735,2.447935058411735,0.2,0.3999999771273954,0.3999999771273954,0.3,0.07288548037982234,0.07288548037982234,2.5,2.031809677600558,2.031809677600558,0.3,0.399999999994134,0.399999999994134,0.3,0.0806454229648127,0.0806454229648127,3.0,3.0955581713143245,3.0955581713143245,0.3,0.39999999989892293,0.39999999989892293,0.3,0.09759693340603837,0.09759693340603837,3.8,3.7000000000154216,3.7000000000154216,0.3,0.39999931341337847,0.39999931341337847
        1.0,0.3384902152130924,0.3384902152130924,0.0,0.017262089305238426,0.017262089305238426,0.1,0.02000000000431808,0.02000000000431808,0.1,0.19999999999707,0.19999999999707,0.3,0.06390170759703961,0.06390170759703961,2.0,1.7470034358646442,1.7470034358646442,0.1,0.29999999999595617,0.29999999999595617,0.3,0.10843271104545171,0.10843271104545171,2.5,2.318373021191109,2.318373021191109,0.2,0.39999999999414,0.39999999999414,0.3,0.0828004001712187,0.0828004001712187,2.5,3.0506627778035975,3.0506627778035975,0.3,0.3999825114407111,0.3999825114407111,0.3,0.039900814326592204,0.039900814326592204,3.0,4.379956884593627,4.379956884593627,0.3,0.3999999999941403,0.3999999999941403,0.3,0.09812726904670366,0.09812726904670366,3.8,3.7000000000154216,3.7000000000154216,0.2,0.39999999999413927,0.39999999999413927
        1.0,0.3383768308405881,0.3383768308405881,0.0,0.017249155005218952,0.017249155005218952,0.1,0.020000223602285063,0.020000223602285063,0.1,0.19999665144901568,0.19999665144901568,0.3,0.05316047862491946,0.05316047862491946,2.0,1.6591127700194552,1.6591127700194552,0.1,0.29999262582163666,0.29999262582163666,0.3,0.08210748667320089,0.08210748667320089,2.5,2.424765205447216,2.424765205447216,0.2,0.39949761254017074,0.39949761254017074,0.3,0.06636980111213131,0.06636980111213131,2.5,2.0669028672740284,2.0669028672740284,0.3,0.39999998671625336,0.39999998671625336,0.3,0.08125492663466871,0.08125492663466871,3.0,3.0662131700347164,3.0662131700347164,0.3,0.39999999999414,0.39999999999414,0.3,0.09830451265206608,0.09830451265206608,3.7,3.700483502444169,3.700483502444169,0.2,0.39999999997262314,0.39999999997262314
    ```

[1]:
  https://lmfit.github.io/lmfit-py/examples/documentation/model_two_components.html#sphx-glr-examples-documentation-model-two-components-py
[2]:
  https://github.com/Anselmoo/spectrafit/blob/main/docs/examples/example9_3.ipynb
