"""Test of CMD and Tool Model."""
from spectrafit.api.cmd_model import CMDModelAPI


def test_default() -> None:
    """Test for default settings of CMD Model."""
    result = CMDModelAPI(infile="").dict()
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


def test_overwrite() -> None:
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
            "model_type": "ga",
            "height": [1],
            "threshold": [0.1],
            "distance": 10,
            "prominence": [1],
            "width": [1],
            "wlen": 1,
        },
    ).dict()
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
    assert result["autopeak"]["model_type"] == "ga"
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
