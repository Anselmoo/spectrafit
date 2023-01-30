"""Test of the RIXS Model API."""

import numpy as np

from spectrafit.api.rixs_model import MainTitleAPI
from spectrafit.api.rixs_model import RIXSPlotAPI
from spectrafit.api.rixs_model import SizeRatioAPI
from spectrafit.api.rixs_model import XAxisAPI
from spectrafit.api.rixs_model import YAxisAPI
from spectrafit.api.rixs_model import ZAxisAPI


def test__axises() -> None:
    """Test the axises."""
    x_api = XAxisAPI(name="test", unit="test_unit")
    y_api = YAxisAPI(name="test", unit="test_unit")
    z_api = ZAxisAPI(name="test", unit="test_unit")

    assert x_api.name == "test"
    assert x_api.unit == "test_unit"
    assert y_api.name == "test"
    assert y_api.unit == "test_unit"
    assert z_api.name == "test"
    assert z_api.unit == "test_unit"


def test_main_title() -> None:
    """Test the main title."""
    title_api = MainTitleAPI(rixs="test", xes="test", xas="test")

    assert title_api.rixs == "test"
    assert title_api.xes == "test"
    assert title_api.xas == "test"


def test_size_ratio() -> None:
    """Test the size ratio."""
    size_ratio_api = SizeRatioAPI(size=(1, 1), ratio_rixs=(1, 1))

    assert size_ratio_api.size == (1, 1)
    assert size_ratio_api.ratio_rixs == (1, 1)


def test_rixs_model() -> None:
    """Test for raising exception of RIXS Model."""
    _model = RIXSPlotAPI(
        incident_energy=np.array([1, 2, 3]),
        emission_energy=np.array([1, 2, 3]),
        emission_intensity=np.meshgrid(np.array([1, 2, 3]), np.array([1, 2, 3]))[0],
        x_axis=XAxisAPI(name="test", unit="test_unit"),
        y_axis=YAxisAPI(name="test", unit="test_unit"),
        z_axis=ZAxisAPI(name="test", unit="test_unit"),
        main_title=MainTitleAPI(rixs="test", xes="test", xas="test"),
        size_ratio=SizeRatioAPI(
            size=(100, 100), ratio_rixs=(2, 2), ratio_xes=(3, 1.5), ratio_xas=(3, 1.5)
        ),
    )
    assert _model.incident_energy.shape == (3,)
    assert _model.emission_energy.shape == (3,)
    assert _model.emission_intensity.shape == (3, 3)
    assert _model.x_axis.name == "test"
    assert _model.x_axis.unit == "test_unit"
    assert _model.y_axis.name == "test"
    assert _model.y_axis.unit == "test_unit"
    assert _model.z_axis.name == "test"
    assert _model.size_ratio.size == (100, 100)
    assert _model.size_ratio.ratio_rixs == (2, 2)
    assert _model.size_ratio.ratio_xes == (3, 1.5)
    assert _model.size_ratio.ratio_xas == (3, 1.5)
