"""Auto-peak detection and model parameter definition for curve fitting.

This module contains classes for automatic peak detection and parameter definition
including `AutoPeakDetection`, `ModelParameters`, and `ReferenceKeys`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import numpy as np

from lmfit import Parameters
from scipy.signal import find_peaks
from scipy.stats import hmean

from spectrafit.api.models_model import DistributionModelAPI
from spectrafit.api.tools_model import AutopeakAPI


if TYPE_CHECKING:
    import pandas as pd

    from numpy.typing import NDArray

# Constants for global fitting modes
GLOBAL_NONE = 0  # No global fitting
GLOBAL_STANDARD = 1  # Standard global fitting
GLOBAL_WITH_PRE = 2  # Global fitting with pre-processing


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting and peak detection."""

    __models__: ClassVar[list[str]] = list(
        DistributionModelAPI.model_json_schema()["properties"].keys(),
    )

    __automodels__: ClassVar[list[str]] = [
        "gaussian",
        "orcagaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
    ]

    # Mössbauer models
    __moessbauer_models__: ClassVar[list[str]] = [
        "moessbauersinglet",
        "moessbauerdoublet",
        "moessbauersextet",
        "moessbaueroctet",
    ]

    def model_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Model name.

        Raises:
            NotImplementedError: If the model is not implemented.

        """
        model_prefix = model.split("_")[0]

        # Check in main models list
        if (
            model_prefix not in self.__models__
            and model_prefix not in self.__moessbauer_models__
        ):
            msg = f"{model} is not supported!"
            raise NotImplementedError(msg)

    def automodel_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Auto Model name (gaussian, orcagaussian,
                lorentzian, voigt, or pseudovoigt).

        Raises:
            KeyError: If the model is not supported.

        """
        if model not in self.__automodels__:
            msg = f"{model} is not supported for auto detection! Use one of {self.__automodels__}"
            raise KeyError(msg)

    def detection_check(self, args: dict[str, Any]) -> None:
        """Check if detection is available.

        Args:
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Raises:
            KeyError: If the key is not parameter of the `scipy.signal.find_peaks`
                function. This will be checked via `pydantic` in `spectrafit.api`.

        """
        AutopeakAPI(**args)


class AutoPeakDetection:
    """Automatic detection of peaks in a spectrum."""

    def __init__(
        self,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        args: dict[str, Any],
    ) -> None:
        """Initialize the AutoPeakDetection class.

        Args:
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.x = x
        self.data = data
        self._args = args["autopeak"]

    @staticmethod
    def check_key_exists(
        key: str,
        args: dict[str, Any],
        value: float | tuple[Any, Any],
    ) -> Any:
        """Check if a key exists in a dictionary.

        Please check for the reference key also [scipy.signal.find_peaks][1].

        [1]:
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html


        Args:
            key (str): Reference key of `scipy.signal.find_peaks`.
            args (Dict[str, Any]): Reference values of `scipy.signal.find_peaks`, if not
                 defined will be set to estimated default values.
            value (Union[float, Tuple[float,float]]): Default value for the reference
                 key.

        Returns:
            Any: The reference value for `scipy.signal.find_peaks`.

        """
        return args.get(key, value)

    @property
    def estimate_height(self) -> tuple[float, float]:
        r"""Estimate the initial height based on an inverse noise ratio of a signal.

        !!! info "About the estimation of the height"

            The lower end of the height is the inverse noise ratio of the `data`, and
            upper limit is the maximum value of the `data`. The noise ratio of the
            `data` is based on the original implementation by `SciPy`:

            ```python
            def signaltonoise(a, axis=0, ddof=0):
                a = np.asanyarray(a)
                m = a.mean(axis)
                sd = a.std(axis=axis, ddof=ddof)
                return np.where(sd == 0, 0, m / sd)
            ```

        Returns:
            Tuple[float, float]: Tuple of the inverse signal to noise ratio and
                 the maximum value of the `data`.

        """
        return 1 - self.data.mean() / self.data.std(), self.data.max()

    @property
    def estimate_threshold(self) -> tuple[float, float]:
        """Estimate the threshold value for the peak detection.

        Returns:
            Tuple[float, float]: Minimum and maximum value of the spectrum `data`,
                 respectively, `intensity`.

        """
        return self.data.min(), self.data.max()

    @property
    def estimate_distance(self) -> float:
        """Estimate the initial distance between peaks.

        Returns:
            float: Estimated distance between peaks.

        """
        min_step = np.diff(self.x).min()
        return max(min_step, 1.0)

    @property
    def estimate_prominence(self) -> tuple[float, float]:
        """Estimate the prominence of a peak.

        !!! info "About the estimation of the prominence"

            The prominence is the difference between the height of the peak and the
            bottom. To get a estimate of the prominence, the height of the peak is
            calculated by maximum value of the `data` and the bottom is calculated by
            the harmonic mean of the `data`.

        Returns:
            Tuple[float, float]: Tuple of the harmonic-mean and maximum value of `data`.

        """
        try:
            return hmean(self.data), self.data.max()
        except ValueError:
            pass
        return self.data.mean(), self.data.max()

    @property
    def estimated_width(self) -> tuple[float, float]:
        """Estimate the width of a peak.

        !!! info "About the estimation of the width"

            The width of a peak is estimated for a lower and an upper end. For the lower
            end, the minimum stepsize is used. For the upper end, the stepsize between
            the half maximum and the minimum value of the `data` is used as the width.

        Returns:
            Tuple[float, float]: Estimated width lower and uper end of the peaks.

        """
        return (
            np.diff(self.x).min(),
            np.abs(self.x[self.data.argmax()] - self.x[self.data.argmin()]) / 2,
        )

    @property
    def estimated_rel_height(self) -> float:
        """Estimate the relative height of a peak.

        !!! info "About the estimation of the relative height"

            The relative height of a peak is approximated by the difference of the
            harmonic mean value of the `data` and the minimum value of the `data`
            divided by the factor of `4`. In case of negative ratios, the value will be
            set to `Zero`.

        Returns:
            float: Estimated relative height of a peak.

        """
        try:
            rel_height = (hmean(self.data) - self.data.min()) / 4
        except ValueError:
            rel_height = (self.data.mean() - self.data.min()) / 4
        return rel_height if rel_height > 0 else 0.0

    @property
    def estimated_wlen(self) -> float:
        r"""Estimate the window length for the peak detection.

        !!! info "About the estimation of the window length"

            The window length is the length of the window for the peak detection is
            defined to be 1% of the length of the `data`, consequently the len of the
            `data` is divided by 100. In case of a window length smaller than 1, the
            window length will be set to numerical value of 1, which is defined by
            `1 + 1e-9`.

        Returns:
            float: Estimated window length is set to the numeric value of > 1.

        """
        wlen = self.data.size / 100
        return wlen if wlen > 1.0 else 1 + 1e-9

    @property
    def estimated_plateau_size(self) -> tuple[float, float]:
        """Estimate the plateau size for the peak detection.

        Returns:
            Tuple[float, float]: Estimated plateau size is set to `zero` for the lower
                 end and the maximum value of the `x` for the upper end.

        """
        return 0.0, self.x.max()

    def initialize_peak_detection(self) -> None:
        """Initialize the peak detection.

        !!! note "Initialize the peak detection"

            This method is used to initialize the peak detection. The initialization can
            be activated by setting the `initialize` attribute to `True`, which will
            automatically estimate the default parameters for the peak detection. In
            case of the `initialize` attribute is defined as dictionary, the proposed
            values are taken from the dictionary if th

        Raise:
            TypeError: If the `initialize` attribute is not of type `bool` or `dict`.
        """
        if isinstance(self._args, bool):
            self.default_values()
        elif isinstance(self._args, dict):
            ReferenceKeys().detection_check(self._args)
            self.height = self.check_key_exists(
                key="height",
                args=self._args,
                value=self.estimate_height,
            )
            self.threshold = self.check_key_exists(
                key="threshold",
                args=self._args,
                value=self.estimate_threshold,
            )
            self.distance = self.check_key_exists(
                key="distance",
                args=self._args,
                value=self.estimate_distance,
            )
            self.prominence = self.check_key_exists(
                key="prominence",
                args=self._args,
                value=self.estimate_prominence,
            )
            self.width = self.check_key_exists(
                key="width",
                args=self._args,
                value=self.estimated_width,
            )
            self.wlen = self.check_key_exists(
                key="wlen",
                args=self._args,
                value=self.estimated_wlen,
            )
            self.rel_height = self.check_key_exists(
                key="rel_height",
                args=self._args,
                value=self.estimated_rel_height,
            )
            self.plateau_size = self.check_key_exists(
                key="plateau_size",
                args=self._args,
                value=0.0,
            )
        else:
            msg = f"The type of the `args` is not supported: {type(self._args)}"
            raise TypeError(msg)

    def default_values(self) -> None:
        """Set the default values for the peak detection."""
        self.height = self.estimate_height
        self.threshold = self.estimate_threshold
        self.distance = self.estimate_distance
        self.prominence = self.estimate_prominence
        self.width = self.estimated_width
        self.wlen = self.estimated_wlen
        self.rel_height = self.estimated_rel_height
        self.plateau_size = 0

    def __autodetect__(self) -> Any:
        """Return peak positions and properties."""
        return find_peaks(
            self.data,
            height=self.height,
            threshold=self.threshold,
            distance=self.distance,
            prominence=self.prominence,
            width=self.width,
            wlen=self.wlen,
            rel_height=self.rel_height,
            plateau_size=self.plateau_size,
        )


class ModelParameters(AutoPeakDetection):
    """Class to define the model parameters."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize the model parameters.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]):
                 Nested arguments dictionary for the model based on **one** or **two**
                 `int` keys depending if global fitting parameters, will explicit
                 defined or not.

        !!! note "About `args` for models"

            The `args` dictionary is used to define the model parameters. And the total
            nested dictionary structure is as follows:

            ```python
            args: Dict[str, Dict[int, Dict[str, Dict[str, Union[str, int, float]]]]]
            ```

        !!! info "About the fitting options"

            In general, there are two option for the fitting possible:

            1. `Classic fitting` or `local fitting`, where the parameters are defined
                for a 2D spectrum.
            2. `Global fitting`, where the parameters are defined for a 3D spectrum.
                Here, the parameters can be automatically defined for each column on the
                basis of the initial parameters or they can be completley defined by the
                user. The `global fitting` definition starts at `1` similiar to the
                peaks attributes notation.

        """
        self.col_len = df.shape[1] - 1
        self.args = args
        self.params = Parameters()
        self.x, self.data = self.df_to_numvalues(df=df, args=args)

        super().__init__(self.x, self.data, self.args)

    def df_to_numvalues(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Transform the dataframe to numeric values of `x` and `data`.

        !!! note "About the dataframe to numeric values"

            The transformation is done by the `value` property of pandas. The dataframe
            is separated into the `x` and `data` columns and the `x` column is
            transformed to the energy values and the `data` column is transformed to
            the intensity values depending on the `args` dictionary. In terms of global
            fitting, the `data` contains the intensity values for each column.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            Tuple[NDArray[np.float64], NDArray[np.float64]]: Tuple of `x` and
                 `data` as numpy arrays.

        """
        if args["global_"]:
            return (
                df[args["column"][0]].to_numpy(),
                df.loc[:, df.columns != args["column"][0]].to_numpy(),
            )
        return (df[args["column"][0]].to_numpy(), df[args["column"][1]].to_numpy())

    @property
    def return_params(self) -> Parameters:
        """Return the `class` representation of the model parameters.

        Returns:
            Parameters: Model parameters class.

        """
        self.__perform__()
        return self.params

    def __str__(self) -> str:
        """Return the `string` representation of the model parameters.

        Returns:
            str: String representation of the model parameters.

        """
        self.__perform__()
        return str(self.params)

    def __perform__(self) -> None:
        """Perform the model parameter definition.

        Raises:
            KeyError: Global fitting is combination with automatic peak detection is
                 not implemented yet.

        """
        if self.args["global_"] == GLOBAL_NONE and not self.args["autopeak"]:
            self.define_parameters()
        elif self.args["global_"] == GLOBAL_STANDARD and not self.args["autopeak"]:
            self.define_parameters_global()
        elif self.args["global_"] == GLOBAL_WITH_PRE and not self.args["autopeak"]:
            self.define_parameters_global_pre()
        elif self.args["global_"] == GLOBAL_NONE:
            self.initialize_peak_detection()
            self.define_parameters_auto()
        elif self.args["global_"] in [GLOBAL_STANDARD, GLOBAL_WITH_PRE]:
            msg = "Global fitting mode with automatic peak detection is not supported yet."
            raise KeyError(msg)

    def define_parameters_auto(self) -> None:  # noqa: C901
        """Auto define the model parameters for local fitting."""
        positions, properties = self.__autodetect__()
        if (
            not isinstance(self.args["autopeak"], bool)
            and "modeltype" in self.args["autopeak"]
        ):
            _model = self.args["autopeak"]["modeltype"].lower()
            ReferenceKeys().automodel_check(model=_model)
            models = _model
        else:
            models = "gaussian"

        if models == "gaussian":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                    strict=False,
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmg_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "orcagaussian":
            for i, (_cent, _amp, _width) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                    strict=False,
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_width_{i}",
                    value=_width,
                    min=0,
                    max=2 * _width,
                    vary=True,
                )
        elif models == "lorentzian":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                    strict=False,
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhml_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "voigt":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                    strict=False,
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmv_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "pseudovoigt":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                    strict=False,
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmg_{i}",
                    value=0.5 * _fhmw,
                    min=0,
                    max=_fhmw,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhml_{i}",
                    value=0.5 * _fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )

        self.args["auto_generated_models"] = {
            "models": {
                key: {
                    "value": self.params[key].value,
                    "min": self.params[key].min,
                    "max": self.params[key].max,
                    "vary": self.params[key].vary,
                }
                for key in self.params
            },
            "positions": positions.tolist(),
            "properties": {key: value.tolist() for key, value in properties.items()},
        }

    def define_parameters(self) -> None:
        """Define the input parameters for a `params`-dictionary for classic fitting."""
        for key_1, value_1 in self.args["peaks"].items():
            self.define_parameters_loop(key_1=key_1, value_1=value_1)

    def define_parameters_loop(self, key_1: str, value_1: dict[str, Any]) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            value_1 (Dict[str, Any]): The value of the first level of the input
                 dictionary.

        """
        for key_2, value_2 in value_1.items():
            self.define_parameters_loop_2(key_1=key_1, key_2=key_2, value_2=value_2)

    def define_parameters_loop_2(
        self,
        key_1: str,
        key_2: str,
        value_2: dict[str, Any],
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            value_2 (Dict[str, Any]): The value of the first level of the input
                 dictionary.

        """
        for key_3, value_3 in value_2.items():
            self.define_parameters_loop_3(
                key_1=key_1,
                key_2=key_2,
                key_3=key_3,
                value_3=value_3,
            )

    def define_parameters_loop_3(
        self,
        key_1: str,
        key_2: str,
        key_3: str,
        value_3: dict[str, Any],
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (Dict[str, Any]): The value of the third level of the input
                 dictionary.

        """
        self.params.add(f"{key_2}_{key_3}_{key_1}", **value_3)

    def define_parameters_global(self) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting."""
        for col_i in range(self.col_len):
            for key_1, value_1 in self.args["peaks"].items():
                for key_2, value_2 in value_1.items():
                    for key_3, value_3 in value_2.items():
                        self._define_parameter(
                            col_i=col_i,
                            key_1=key_1,
                            key_2=key_2,
                            key_3=key_3,
                            value_3=value_3,
                        )

    def _define_parameter(
        self,
        col_i: int,
        key_1: str,
        key_2: str,
        key_3: str,
        value_3: dict[str, Any],
    ) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting.

        Args:
            col_i (int): The column index.
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (Dict[str, Any]): The value of the third level of the input
                 dictionary.

        """
        if col_i:
            if key_3 != "amplitude":
                self.params.add(
                    f"{key_2}_{key_3}_{key_1}_{col_i + 1}",
                    expr=f"{key_2}_{key_3}_{key_1}_1",
                )
            else:
                self.params.add(
                    f"{key_2}_{key_3}_{key_1}_{col_i + 1}",
                    **value_3,
                )

        else:
            self.params.add(f"{key_2}_{key_3}_{key_1}_1", **value_3)

    def define_parameters_global_pre(self) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting.

        !!! warning "About `params` for global fitting"

            `define_parameters_global_pre` requires fully defined `params`-dictionary
            in the json, toml, or yaml file input. This means:

            1. Number of the spectra must be defined.
            2. Number of the peaks must be defined.
            3. Number of the parameters must be defined.
            4. The parameters must be defined.
        """
        for key_1, value_1 in self.args["peaks"].items():
            for key_2, value_2 in value_1.items():
                for key_3, value_3 in value_2.items():
                    for key_4, value_4 in value_3.items():
                        self.params.add(f"{key_3}_{key_4}_{key_2}_{key_1}", **value_4)
