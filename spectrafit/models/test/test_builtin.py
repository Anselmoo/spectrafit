"""Pytest of the model-module."""

from __future__ import annotations

from math import isclose
from math import log
from math import pi
from math import sqrt
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from lmfit import Minimizer
from lmfit import Parameters

from spectrafit.models.builtin import Constants
from spectrafit.models.builtin import DistributionModels
from spectrafit.models.builtin import ModelParameters
from spectrafit.models.builtin import SolverModels
from spectrafit.models.builtin import calculated_model
from spectrafit.test.fixtures import FittingFixture
from spectrafit.test.fixtures import ParameterSpec
from spectrafit.test.fixtures import PeakSpec


if TYPE_CHECKING:
    from numpy.typing import NDArray


def assert_solver_models(mp: tuple[Minimizer, Any]) -> None:
    """Assert SolverModels."""
    assert isinstance(mp.__str__(), str)
    assert isinstance(mp, tuple)


@pytest.fixture
def random_df() -> pd.DataFrame:
    """Fixture for random dataframe."""
    return pd.DataFrame(
        {
            "Energy": np.arange(100).astype(np.float64),
            "Intensity_1": np.random.default_rng(101).random(100),
            "Intensity_2": np.random.default_rng(102).random(100),
            "Intensity_3": np.random.default_rng(103).random(100),
            "Intensity_4": np.random.default_rng(104).random(100),
        },
    )


class TestConstants:
    """Test constants."""

    def test_ln2(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.ln2, log(2.0), rel_tol=1e-5)

    def test_sq2pi(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.sq2pi, sqrt(2.0 * pi), rel_tol=1e-5)

    def test_sqpi(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.sqpi, sqrt(pi), rel_tol=1e-5)

    def test_sq2(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.sq2, sqrt(2.0), rel_tol=1e-5)

    def test_fwhmg2sig(self) -> None:
        """Test the Constants class."""
        assert isclose(
            Constants.fwhmg2sig,
            1 / (2.0 * sqrt(2.0 * log(2.0))),
            rel_tol=1e-5,
        )

    def test_fwhml2sig(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.fwhml2sig, 1 / 2.0, rel_tol=1e-5)

    def test_fwhmv2sig(self) -> None:
        """Test the Constants class."""
        assert isclose(Constants.fwhmv2sig, 1 / 3.60131, rel_tol=1e-5)


class TestNotSupported:
    """Test of not supported models."""

    # Using ClassVar per Ruff RUF012 even though mypy complains
    args: ClassVar[dict[str, Any]] = FittingFixture(
        peaks=[
            PeakSpec(
                model_name="dummy",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=0.1, min=0.00002, max=2.5),
                    "fwhml": ParameterSpec(value=1, min=0.00001, max=2.5),
                },
            ),
        ],
        minimizer={"method": "Nelder-Mead", "tol": 1e-6},
        optimizer={"method": "Nelder-Mead", "tol": 1e-6},
    ).to_input_dict()
    df = pd.DataFrame(
        {
            "energy": np.arange(10),
            "intensity": np.random.default_rng(42).standard_normal((10,)),
        },
    )

    def test_solver_model_exit_local(self) -> None:
        """Exit-Test of solver_model for local fitting."""
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df,
                args=self.args,
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1 is not supported!"

    def test_solver_model_exit_global(self) -> None:
        """Exit-Test of solver_model for global fitting."""
        _args = self.args
        _args["global_"] = 1
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df,
                args=_args,
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1_1 is not supported!"

    def test_calculated_model_exit(self) -> None:
        """Exit-Test of solver_model."""
        params = Parameters()
        params.add("dummy_amplitude_1", value=1.0)
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            calculated_model(
                params=params,
                x=self.df["energy"].values,
                df=self.df["intensity"].values,
                global_fit=0,
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1 is not supported!"


class TestModelParametersSolver:
    """Test of model parameters."""

    # Using ClassVar per Ruff RUF012 even though mypy complains
    args: ClassVar[dict[str, Any]] = FittingFixture(
        peaks=[
            PeakSpec(
                model_name="pseudovoigt",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=0.1, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="pseudovoigt",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                    "fwhml": ParameterSpec(value=0.01, min=0.0001, max=2.5),
                },
            ),
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
        ],
        minimizer={"nan_policy": "propagate", "calc_covar": False},
        optimizer={"max_nfev": 10, "method": "leastsq"},
    ).to_input_dict() | {"column": ["Energy", "Intensity"]}
    args_global_1: ClassVar[dict[str, Any]] = FittingFixture(
        peaks=[
            PeakSpec(
                model_name="pseudovoigt",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=0.1, min=0.00002, max=2.5),
                    "fwhml": ParameterSpec(value=1, min=0.00001, max=2.5),
                },
            ),
            PeakSpec(
                model_name="pseudovoigt",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                    "fwhml": ParameterSpec(value=0.01, min=0.0001, max=2.5),
                },
            ),
        ],
        minimizer={"nan_policy": "propagate", "calc_covar": False},
        optimizer={"max_nfev": 10, "method": "leastsq"},
    ).to_input_dict() | {"global_": 1, "column": ["Energy"]}
    args_global_2: ClassVar[dict[str, Any]] = {
        "global_": 2,
        "column": ["Energy"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "peaks": {
            "1": {
                "1": {
                    "pseudovoigt": {
                        "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                        "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 0.1,
                        },
                        "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                    },
                },
                "2": {
                    "pseudovoigt": {
                        "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                        "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                        "fwhml": {
                            "max": 2.5,
                            "min": 0.0001,
                            "vary": True,
                            "value": 0.01,
                        },
                    },
                },
            },
        },
    }
    df = pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity": np.random.default_rng(10).random(10),
        },
    )
    df_global = pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity_1": np.random.default_rng(1).random(10),
            "Intensity_2": np.random.default_rng(2).random(10),
            "Intensity_3": np.random.default_rng(3).random(10),
            "Intensity_4": np.random.default_rng(4).random(10),
        },
    )

    def test_str_return(self) -> None:
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert isinstance(mp.__str__(), str)

    def test_param_return(self) -> None:
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert str(type(mp.return_params)) == "<class 'lmfit.parameter.Parameters'>"

    def test_len_param_normal(self) -> None:
        """Test of length of the paramaters for normal fitting."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert len(mp.return_params.keys()) == 10

    def test_len_param_global_1(self) -> None:
        """Test of length of the paramaters for global fitting."""
        mp = ModelParameters(df=self.df_global, args=self.args_global_1)
        mp.define_parameters_global()
        assert len(mp.return_params.keys()) == 32

    def test_solver_local(self) -> None:
        """Test of SolverModels for local fitting."""
        mp = SolverModels(df=self.df, args=self.args)()
        assert_solver_models(mp)

    def test_solver_global_1(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_1)()
        assert_solver_models(mp)

    def test_solver_global_2(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_2)()
        assert_solver_models(mp)

    @pytest.fixture
    def args_setting(self) -> dict[str, Any]:
        """Fixture for args built from Pydantic fixture models.

        Returns:
            dict[str, Any]: Minimizer, optimizer, and peaks for testing.

        """
        _peaks = [
            PeakSpec(
                model_name="pseudovoigt",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                    "fwhml": ParameterSpec(value=0.01, min=0.0001, max=2.5),
                },
            ),
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmg": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="lorentzian",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhml": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="exponential",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "decay": ParameterSpec(value=0, min=-200, max=200),
                    "intercept": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="power",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "exponent": ParameterSpec(value=0, min=-200, max=200),
                    "intercept": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="linear",
                parameters={
                    "slope": ParameterSpec(value=1, min=0, max=200),
                    "intercept": ParameterSpec(value=1, min=0, max=200),
                },
            ),
            PeakSpec(
                model_name="constant",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                },
            ),
            PeakSpec(
                model_name="erf",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "sigma": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="atan",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "sigma": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="log",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "sigma": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="heaviside",
                parameters={
                    "amplitude": ParameterSpec(value=1, min=0, max=200),
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "sigma": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="voigt",
                parameters={
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmv": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                    "gamma": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
            PeakSpec(
                model_name="voigt",
                parameters={
                    "center": ParameterSpec(value=0, min=-200, max=200),
                    "fwhmv": ParameterSpec(value=1.0, min=0.00002, max=2.5),
                },
            ),
        ]
        return {
            "minimizer": {"nan_policy": "propagate", "calc_covar": False},
            "optimizer": {"max_nfev": 10, "method": "leastsq"},
            "peaks": {
                str(i): peak.to_dict() for i, peak in enumerate(_peaks, start=1)
            },
        }

    def test_all_model_local(
        self,
        random_df: pd.DataFrame,
        args_setting: dict[str, Any],
    ) -> None:
        """Test of the AllModel class for local fitting."""
        df = random_df
        args = {
            "global_": 0,
            "column": ["Energy", "Intensity_1"],
            **args_setting,
        }
        mp = SolverModels(df=df, args=args)()
        assert_solver_models(mp)

    def test_all_model_global(
        self,
        random_df: pd.DataFrame,
        args_setting: dict[str, Any],
    ) -> None:
        """Test of the AllModel class for global fitting."""
        df = random_df
        args = {
            "global_": 1,
            "column": ["Energy"],
            **args_setting,
        }

        mp = SolverModels(df=df, args=args)()
        assert_solver_models(mp)


class TestModel:
    """Test the distribution class and its models."""

    @pytest.fixture
    def x_data(self) -> NDArray[np.float64]:
        """Create x data."""
        return np.linspace(0, 10, 100, dtype=float)

    @pytest.fixture
    def df_data(self) -> pd.DataFrame:
        """Create x,y data."""
        return pd.DataFrame(
            {
                "Energy": np.linspace(0, 10, 100, dtype=float),
                "Intensity": np.linspace(0, 10, 100, dtype=float),
            },
        )

    @pytest.mark.parametrize(
        ("model", "params"),
        [
            ("gaussian", {"amplitude": 1.0, "center": 5.0, "fwhmg": 1.0}),
            ("orcagaussian", {"amplitude": 1.0, "center": 5.0, "width": 1.0}),
            ("lorentzian", {"amplitude": 1.0, "center": 5.0, "fwhml": 1.0}),
            ("voigt", {"center": 5.0, "fwhmv": 1.0, "gamma": 1}),
            (
                "pseudovoigt",
                {"amplitude": 1.0, "center": 5.0, "fwhmg": 1, "fwhml": 1.0},
            ),
            ("exponential", {"amplitude": 1.0, "decay": 1, "intercept": 1.0}),
            ("power", {"amplitude": 1.0, "exponent": 1.0, "intercept": 1.0}),
            ("linear", {"slope": 1.0, "intercept": 1.0}),
            ("constant", {"amplitude": 1.0}),
            ("erf", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("heaviside", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("atan", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("log", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("cgaussian", {"amplitude": 1.0, "center": 5.0, "fwhmg": 1.0}),
            ("clorentzian", {"amplitude": 1.0, "center": 5.0, "fwhml": 1.0}),
            ("cvoigt", {"amplitude": 1.0, "center": 5.0, "fwhmv": 1.0}),
            (
                "polynom2",
                {"coefficient0": 1.0, "coefficient1": 1.0, "coefficient2": 1.0},
            ),
            (
                "polynom3",
                {
                    "coefficient0": 1.0,
                    "coefficient1": 1.0,
                    "coefficient2": 1.0,
                    "coefficient3": 1.0,
                },
            ),
            (
                "pearson1",
                {"amplitude": 1.0, "center": 5.0, "sigma": 1.0, "exponent": 1.0},
            ),
            (
                "pearson2",
                {"amplitude": -1.0, "center": 2.5, "sigma": 1.2, "exponent": -1.0},
            ),
            (
                "pearson3",
                {
                    "amplitude": 1.0,
                    "center": 5.0,
                    "sigma": 1.0,
                    "exponent": 1.0,
                    "skewness": 1.0,
                },
            ),
            (
                "pearson4",
                {
                    "amplitude": 1.0,
                    "center": 5.0,
                    "sigma": -1.0,
                    "exponent": 1.0,
                    "skewness": -1.0,
                    "kurtosis": 1.0,
                },
            ),
        ],
    )
    def test_distrubtion_models(
        self,
        x_data: NDArray[np.float64],
        model: str,
        params: dict[str, float],
    ) -> None:
        """Test of all distribution models."""
        y_data = getattr(DistributionModels(), model)(x_data, **params)
        assert isinstance(y_data, np.ndarray)
        assert len(y_data) == 100

    @pytest.mark.parametrize(
        ("model", "params"),
        [
            ("gaussian", {"amplitude": {}, "center": {}, "fwhmg": {}}),
            ("orcagaussian", {"amplitude": {}, "center": {}, "width": {}}),
            ("lorentzian", {"amplitude": {}, "center": {}, "fwhml": {}}),
            ("voigt", {"center": {}, "fwhmv": {}, "gamma": {}}),
            (
                "pseudovoigt",
                {"amplitude": {}, "center": {}, "fwhmg": {}, "fwhml": {}},
            ),
            ("exponential", {"amplitude": {}, "decay": {}, "intercept": {}}),
            ("power", {"amplitude": {}, "exponent": {}, "intercept": {}}),
            ("linear", {"slope": {}, "intercept": {}}),
            ("constant", {"amplitude": {}}),
            ("erf", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("heaviside", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("atan", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("log", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("cgaussian", {"amplitude": {}, "center": {}, "fwhmg": {}}),
            ("clorentzian", {"amplitude": {}, "center": {}, "fwhml": {}}),
            ("cvoigt", {"amplitude": {}, "center": {}, "fwhmv": {}}),
            (
                "polynom2",
                {"coefficient0": {}, "coefficient1": {}, "coefficient2": {}},
            ),
            (
                "polynom3",
                {
                    "coefficient0": {},
                    "coefficient1": {},
                    "coefficient2": {},
                    "coefficient3": {},
                },
            ),
            (
                "pearson1",
                {"amplitude": {}, "center": {}, "sigma": {}, "exponent": {}},
            ),
            (
                "pearson2",
                {"amplitude": {}, "center": {}, "sigma": {}, "exponent": {}},
            ),
            (
                "pearson3",
                {
                    "amplitude": {},
                    "center": {},
                    "sigma": {},
                    "exponent": {},
                    "skewness": {},
                },
            ),
            (
                "pearson4",
                {
                    "amplitude": {},
                    "center": {},
                    "sigma": {},
                    "exponent": {},
                    "skewness": {},
                    "kurtosis": {},
                },
            ),
        ],
    )
    def test_model_exitst(
        self,
        df_data: pd.DataFrame,
        model: str,
        params: dict[str, dict[Any, Any]],
    ) -> None:
        """Test if the model exists."""
        args = {
            "global_": 0,
            "column": ["Energy", "Intensity"],
            "minimizer": {"nan_policy": "propagate", "calc_covar": False},
            "optimizer": {"max_nfev": 10, "method": "leastsq"},
            "peaks": {"1": {model: params}},
        }
        mp = SolverModels(df=df_data, args=args)()

        assert_solver_models(mp)
        assert len(mp) == 2
        for name in mp[0].params:
            assert model in name
