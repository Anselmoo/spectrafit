"""Tests for configuration models."""

from __future__ import annotations

import pytest

from pydantic import ValidationError

from spectrafit.api.config_model import CLIConfig
from spectrafit.api.config_model import OutputConfig
from spectrafit.api.config_model import PipelineConfig


class TestOutputConfig:
    """Tests for OutputConfig model."""

    def test_default_values(self) -> None:
        """Test OutputConfig with default values."""
        config = OutputConfig()
        assert config.outfile == "spectrafit_results"
        assert config.formats == ["csv"]
        assert config.save_figures is False
        assert config.figure_format == "png"
        assert config.figure_dpi == 300
        assert config.noplot is False
        assert config.verbose == 1
        assert config.export_residuals is True
        assert config.export_components is True
        assert config.decimal_places == 6

    def test_custom_values(self) -> None:
        """Test OutputConfig with custom values."""
        config = OutputConfig(
            outfile="my_results",
            formats=["csv", "json", "xlsx"],
            save_figures=True,
            figure_format="pdf",
            figure_dpi=600,
            noplot=True,
            verbose=2,
            export_residuals=False,
            export_components=False,
            decimal_places=4,
        )
        assert config.outfile == "my_results"
        assert config.formats == ["csv", "json", "xlsx"]
        assert config.save_figures is True
        assert config.figure_format == "pdf"
        assert config.figure_dpi == 600
        assert config.noplot is True
        assert config.verbose == 2
        assert config.export_residuals is False
        assert config.export_components is False
        assert config.decimal_places == 4

    def test_dpi_validation(self) -> None:
        """Test DPI range validation."""
        # Valid DPI
        config = OutputConfig(figure_dpi=300)
        assert config.figure_dpi == 300

        # Test minimum boundary
        config = OutputConfig(figure_dpi=72)
        assert config.figure_dpi == 72

        # Test maximum boundary
        config = OutputConfig(figure_dpi=600)
        assert config.figure_dpi == 600

        # DPI below minimum should fail
        with pytest.raises(ValidationError):
            OutputConfig(figure_dpi=50)

        # DPI above maximum should fail
        with pytest.raises(ValidationError):
            OutputConfig(figure_dpi=700)

    def test_verbose_validation(self) -> None:
        """Test verbose level validation."""
        # Valid verbose levels
        for level in [0, 1, 2]:
            config = OutputConfig(verbose=level)
            assert config.verbose == level

        # Invalid verbose level
        with pytest.raises(ValidationError):
            OutputConfig(verbose=3)

        with pytest.raises(ValidationError):
            OutputConfig(verbose=-1)

    def test_decimal_places_validation(self) -> None:
        """Test decimal places validation."""
        # Valid decimal places
        config = OutputConfig(decimal_places=6)
        assert config.decimal_places == 6

        # Test boundaries
        config = OutputConfig(decimal_places=1)
        assert config.decimal_places == 1

        config = OutputConfig(decimal_places=15)
        assert config.decimal_places == 15

        # Invalid decimal places
        with pytest.raises(ValidationError):
            OutputConfig(decimal_places=0)

        with pytest.raises(ValidationError):
            OutputConfig(decimal_places=16)


class TestPipelineConfig:
    """Tests for PipelineConfig model."""

    def test_minimal_config(self) -> None:
        """Test PipelineConfig with minimal required fields."""
        config = PipelineConfig(infile="data.txt")
        assert config.infile == "data.txt"
        assert config.input == "fitting_input.toml"
        assert config.outfile == "spectrafit_results"
        assert config.preprocessing == {}
        assert config.fitting == {}
        assert config.output == {}
        assert config.description is None
        assert config.autopeak is False

    def test_full_config(self) -> None:
        """Test PipelineConfig with all fields."""
        config = PipelineConfig(
            infile="data.txt",
            input="params.json",
            outfile="results",
            preprocessing={"smooth": 5, "shift": 0.1},
            fitting={"method": "leastsq", "max_nfev": 1000},
            output={"formats": ["csv", "json"], "verbose": 2},
            description={"project": "test", "author": "user"},
            autopeak={"height": [0.1, 0.5]},
        )
        assert config.infile == "data.txt"
        assert config.input == "params.json"
        assert config.outfile == "results"
        assert config.preprocessing == {"smooth": 5, "shift": 0.1}
        assert config.fitting == {"method": "leastsq", "max_nfev": 1000}
        assert config.output == {"formats": ["csv", "json"], "verbose": 2}
        assert config.description == {"project": "test", "author": "user"}
        assert config.autopeak == {"height": [0.1, 0.5]}

    def test_output_config_integration(self) -> None:
        """Test PipelineConfig with OutputConfig instance."""
        output_cfg = OutputConfig(
            outfile="my_output",
            formats=["json"],
            verbose=2,
        )
        config = PipelineConfig(
            infile="data.txt",
            output=output_cfg,
        )
        assert isinstance(config.output, OutputConfig)
        assert config.output.outfile == "my_output"
        assert config.output.formats == ["json"]
        assert config.output.verbose == 2


class TestCLIConfig:
    """Tests for CLIConfig model."""

    def test_minimal_config(self) -> None:
        """Test CLIConfig with minimal required fields."""
        config = CLIConfig(infile="data.txt")
        assert config.infile == "data.txt"
        assert config.outfile == "spectrafit_results"
        assert config.input == "fitting_input.toml"
        assert config.oversampling is False
        assert config.energy_start is None
        assert config.energy_stop is None
        assert config.smooth == 0
        assert config.shift == 0
        assert config.column == [0, 1]
        assert config.separator == "\t"
        assert config.decimal == "."
        assert config.header is None
        assert config.comment is None
        assert config.global_ == 0
        assert config.autopeak is False
        assert config.noplot is False
        assert config.verbose == 0
        assert config.description is None

    def test_full_config(self) -> None:
        """Test CLIConfig with all fields."""
        config = CLIConfig(
            infile="data.txt",
            outfile="results",
            input="params.toml",
            oversampling=True,
            energy_start=100.0,
            energy_stop=200.0,
            smooth=5,
            shift=0.5,
            column=["energy", "intensity"],
            separator=",",
            decimal=".",
            header=0,
            comment="#",
            global_=1,
            autopeak={"height": [0.1]},
            noplot=True,
            verbose=2,
            description={"project": "test"},
        )
        assert config.infile == "data.txt"
        assert config.outfile == "results"
        assert config.input == "params.toml"
        assert config.oversampling is True
        assert config.energy_start == 100.0
        assert config.energy_stop == 200.0
        assert config.smooth == 5
        assert config.shift == 0.5
        assert config.column == ["energy", "intensity"]
        assert config.separator == ","
        assert config.decimal == "."
        assert config.header == 0
        assert config.comment == "#"
        assert config.global_ == 1
        assert config.autopeak == {"height": [0.1]}
        assert config.noplot is True
        assert config.verbose == 2
        assert config.description == {"project": "test"}

    def test_global_validation(self) -> None:
        """Test global fitting mode validation."""
        # Valid global modes
        for mode in [0, 1, 2]:
            config = CLIConfig(infile="data.txt", global_=mode)
            assert config.global_ == mode

        # Invalid global mode
        with pytest.raises(ValidationError):
            CLIConfig(infile="data.txt", global_=3)

        with pytest.raises(ValidationError):
            CLIConfig(infile="data.txt", global_=-1)

    def test_smooth_validation(self) -> None:
        """Test smooth parameter validation."""
        # Valid smooth values
        config = CLIConfig(infile="data.txt", smooth=0)
        assert config.smooth == 0

        config = CLIConfig(infile="data.txt", smooth=10)
        assert config.smooth == 10

        # Negative smooth should fail
        with pytest.raises(ValidationError):
            CLIConfig(infile="data.txt", smooth=-1)

    def test_verbose_validation(self) -> None:
        """Test verbose level validation."""
        # Valid verbose levels
        for level in [0, 1, 2]:
            config = CLIConfig(infile="data.txt", verbose=level)
            assert config.verbose == level

        # Invalid verbose level
        with pytest.raises(ValidationError):
            CLIConfig(infile="data.txt", verbose=3)

        with pytest.raises(ValidationError):
            CLIConfig(infile="data.txt", verbose=-1)

    def test_model_dump(self) -> None:
        """Test model serialization using model_dump."""
        config = CLIConfig(
            infile="data.txt",
            outfile="results",
            verbose=2,
        )
        dumped = config.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["infile"] == "data.txt"
        assert dumped["outfile"] == "results"
        assert dumped["verbose"] == 2

    def test_model_dump_exclude_none(self) -> None:
        """Test model serialization excluding None values."""
        config = CLIConfig(infile="data.txt")
        dumped = config.model_dump(exclude_none=True)
        assert isinstance(dumped, dict)
        assert "energy_start" not in dumped
        assert "energy_stop" not in dumped
        assert "header" not in dumped
        assert "comment" not in dumped
        assert "description" not in dumped
