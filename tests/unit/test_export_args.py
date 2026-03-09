"""Unit tests for :mod:`spectrafit.models.export_args`.

These tests pin the expected shape of the pipeline result dict that flows into
:class:`~spectrafit.core.export.SaveResult`, ensuring that future changes to
the pipeline output do not silently break the export layer.
"""

from __future__ import annotations

import pytest

from pydantic import ValidationError

from spectrafit.models.export_args import SaveResultArgs
from spectrafit.models.results.fit_summary import FitInsightsReport
from spectrafit.models.results.fit_summary import SplitOrientFrame


_SPLIT_FRAME: dict[str, object] = {
    "index": [0, 1, 2],
    "columns": ["energy", "data", "best_fit"],
    "data": [[1.0, 2.0, 2.1], [2.0, 3.0, 3.0], [3.0, 4.0, 4.2]],
}

_FIT_INSIGHTS: dict[str, object] = {
    "statistics": {
        "chi_square": 0.123,
        "reduced_chi_square": 0.012,
        "akaike_information": -45.6,
        "bayesian_information": -42.3,
    },
    "variables": {
        "p1_amplitude": {
            "init_value": 1.0,
            "model_value": 1.05,
            "best_value": 1.05,
            "stderr": 0.02,
        },
        "p1_center": {
            "init_value": 300.0,
            "model_value": 300.1,
            "best_value": 300.1,
            "stderr": 0.05,
        },
    },
}

_MINIMAL_ARGS: dict[str, object] = {"outfile": "/tmp/test_run"}

_FULL_ARGS: dict[str, object] = {
    "outfile": "/tmp/test_run",
    "linear_correlation": _SPLIT_FRAME,
    "fit_insights": _FIT_INSIGHTS,
    "regression_metrics": _SPLIT_FRAME,
    "descriptive_statistic": _SPLIT_FRAME,
    # Extra pipeline keys (preserved via extra="allow")
    "global_": 0,
    "peaks": {"p1": {"model_type": "gaussian"}},
    "_bundle": None,
}


@pytest.mark.unit
class TestSaveResultArgsMinimal:
    """Validate minimal construction (only outfile required)."""

    def test_minimal_from_dict(self) -> None:
        """outfile-only dict validates without error."""
        args = SaveResultArgs.model_validate(_MINIMAL_ARGS)
        assert args.outfile == "/tmp/test_run"

    def test_defaults_are_empty_models(self) -> None:
        """Omitted fields default to empty Pydantic models (not None)."""
        args = SaveResultArgs.model_validate(_MINIMAL_ARGS)
        assert isinstance(args.linear_correlation, SplitOrientFrame)
        assert isinstance(args.fit_insights, FitInsightsReport)
        assert isinstance(args.regression_metrics, SplitOrientFrame)
        assert isinstance(args.descriptive_statistic, SplitOrientFrame)

    def test_missing_outfile_raises(self) -> None:
        """Omitting outfile raises ValidationError."""
        with pytest.raises(ValidationError, match="outfile"):
            SaveResultArgs.model_validate({})


@pytest.mark.unit
class TestSaveResultArgsFull:
    """Validate full pipeline result dict construction."""

    @pytest.fixture
    def full_args(self) -> SaveResultArgs:
        return SaveResultArgs.model_validate(_FULL_ARGS)

    def test_outfile(self, full_args: SaveResultArgs) -> None:
        assert full_args.outfile == "/tmp/test_run"

    def test_linear_correlation_typed(self, full_args: SaveResultArgs) -> None:
        """linear_correlation is a SplitOrientFrame, not a raw dict."""
        assert isinstance(full_args.linear_correlation, SplitOrientFrame)
        assert full_args.linear_correlation.columns == ["energy", "data", "best_fit"]

    def test_fit_insights_typed(self, full_args: SaveResultArgs) -> None:
        """fit_insights is a FitInsightsReport with typed variables."""
        assert isinstance(full_args.fit_insights, FitInsightsReport)
        stats = full_args.fit_insights.statistics
        assert stats.chi_square == pytest.approx(0.123)
        assert "p1_amplitude" in full_args.fit_insights.variables

    def test_extra_keys_preserved(self, full_args: SaveResultArgs) -> None:
        """Pipeline-only keys survive round-trip via model_dump."""
        dumped = full_args.model_dump()
        assert dumped["global_"] == 0
        assert "peaks" in dumped


@pytest.mark.unit
class TestSaveResultArgsRoundTrip:
    """model_dump() produces a dict that re-validates cleanly."""

    @pytest.mark.parametrize("args_dict", [_MINIMAL_ARGS, _FULL_ARGS])
    def test_round_trip(self, args_dict: dict[str, object]) -> None:
        args = SaveResultArgs.model_validate(args_dict)
        dumped = args.model_dump()
        re_validated = SaveResultArgs.model_validate(dumped)
        assert re_validated.outfile == args.outfile

    def test_no_cast_in_export_args_module(self) -> None:
        """Regression guard: export_args.py must never use cast()."""
        import ast
        import inspect

        import spectrafit.models.export_args as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        cast_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "cast"
        ]
        assert cast_calls == [], "export_args.py must not contain cast() calls"
