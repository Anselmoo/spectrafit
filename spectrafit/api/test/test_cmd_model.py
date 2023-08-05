"""Test of CMD and Tool Model."""


from getpass import getuser
from hashlib import sha256
from socket import gethostname
from typing import Any

import pytest

from spectrafit import __version__
from spectrafit.api.cmd_model import CMDModelAPI
from spectrafit.api.cmd_model import DescriptionAPI


def test_default_cmd() -> None:
    """Test for default settings of CMD Model."""
    result = CMDModelAPI(infile="").model_dump()
    assert result["infile"] == ""
    assert result["outfile"] == "spectrafit_results"
    assert result["input"] == "fitting_input.toml"
    assert result["oversampling"] is False
    assert result["energy_start"] is None
    assert result["energy_stop"] is None
    assert result["smooth"] == 0
    assert result["shift"] == 0
    assert result["column"] == [0, 1]
    assert result["separator"] == "\t"
    assert result["decimal"] == "."
    assert result["autopeak"] is False


def test_overwrite_cmd() -> None:
    """Test for overwriting settings of CMD Model."""
    result = CMDModelAPI(
        infile="",
        outfile="test",
        oversampling=True,
        energy_start=-1,
        energy_stop=1,
        smooth=10,
        shift=1,
        column=["col_1", "col_2"],
        separator="s+",
        autopeak={
            "modeltype": "ga",
            "height": [1],
            "threshold": [0.1],
            "distance": 10,
            "prominence": [1],
            "width": [1],
            "wlen": 1,
        },
    ).model_dump()
    assert result["infile"] == ""
    assert result["outfile"] == "test"
    assert result["input"] == "fitting_input.toml"
    assert result["oversampling"] is True
    assert result["energy_start"] == -1
    assert result["energy_stop"] == 1
    assert result["smooth"] == 10
    assert result["shift"] == 1
    assert result["column"] == ["col_1", "col_2"]
    assert result["separator"] == "s+"
    assert result["decimal"] == "."
    assert result["autopeak"]["modeltype"] == "ga"
    assert result["autopeak"]["height"] == [1]
    assert result["autopeak"]["threshold"] == [0.1]
    assert result["autopeak"]["distance"] == 10
    assert result["autopeak"]["prominence"] == [1]
    assert result["autopeak"]["width"] == [1]
    assert result["autopeak"]["wlen"] == 1


def test_global_fit() -> None:
    """Test for global fitting settings of CMD Model."""
    result = CMDModelAPI(infile="")
    result.global_ = 1
    assert result.dict()["global_"] == 1


def test_sha256() -> None:
    """Test for sha256 of CMD Model."""
    assert (
        DescriptionAPI().host_info
        == sha256(f"{getuser()}@{gethostname()}".encode()).hexdigest()
    )


def test_default_description() -> None:
    """Test for default settings of Description Model."""
    result = DescriptionAPI().model_dump()
    assert result["project_name"] == "FittingProject"
    assert result["project_details"] == f"Fitting Project via SpectraFit v{__version__}"
    assert result["keywords"] == ["spectra"]
    assert result["authors"] == ["authors"]
    assert result["references"] == ["https://github.com/Anselmoo/spectrafit"]
    assert result["metadata"] is None
    assert result["license"] == "BSD-3-Clause"
    assert result["version"] == __version__


@pytest.mark.parametrize("metadata", [{"test": "test"}, ["test"]])
def test_overwrite_description(metadata: Any) -> None:
    """Test for overwriting settings of Description Model."""
    result = DescriptionAPI(metadata=metadata).model_dump()
    assert result["metadata"] == metadata


@pytest.mark.parametrize(
    "refs",
    [
        ["https://dummy.com/"],
        ["https://dummy.com/", "https://dummy.io/"],
        ["http://dummy.com/", "http://dummy.io/"],
    ],
)
def test_overwrite_references(refs: Any) -> None:
    """Test for overwriting settings of Description Model."""
    result = DescriptionAPI(refs=refs).model_dump()
    assert result["references"] == refs


def test_illegal_references() -> None:
    """Test for illegal references of Description Model."""
    with pytest.raises(ValueError) as exc:
        DescriptionAPI(refs=["dummy.com"])
    assert "dummy.com" in str(exc.value)
