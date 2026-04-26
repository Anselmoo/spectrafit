"""Focused tests for config/context normalization boundaries."""

from __future__ import annotations

import pytest

from pydantic import ValidationError
from spectrafit.adapters.unified_config_input import (
    normalize_strict_unified_config_input,
)
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.fitting_context import coerce_legacy_fitting_context
from spectrafit.models.fitting_context import coerce_legacy_fitting_mode
from spectrafit.models.plot_config import PlotConfig
from spectrafit.models.solver_config import SolverConfig


class TestFittingContextCoercion:
    """Legacy fitting-mode coercion lives in canonical fitting-context helpers."""

    @pytest.mark.parametrize(
        ("raw_value", "expected"),
        [
            (0, FittingMode.STANDARD),
            (1, FittingMode.GLOBAL),
            (True, FittingMode.GLOBAL),
        ],
    )
    def test_coerce_legacy_fitting_mode_accepts_legacy_values(
        self, raw_value: object, expected: FittingMode
    ) -> None:
        assert coerce_legacy_fitting_mode(raw_value) == expected

    def test_coerce_legacy_fitting_context_returns_global_context(self) -> None:
        context = coerce_legacy_fitting_context(1)

        assert context == FittingContext(mode=FittingMode.GLOBAL, n_datasets=2)

    def test_fitting_context_from_global_int_roundtrips_canonical_context(self) -> None:
        context = FittingContext(mode=FittingMode.GLOBAL, n_datasets=3)
        projected = FittingContext.from_global_int(context.global_int)

        assert projected.mode == FittingMode.GLOBAL
        assert projected.n_datasets == 2
        assert projected.model_copy(update={"n_datasets": 3}) == context

    def test_solver_config_stays_canonical_without_global_mode_boundary(self) -> None:
        solver_config = SolverConfig()

        assert solver_config == SolverConfig(
            minimizer=solver_config.minimizer,
            optimizer=solver_config.optimizer,
        )


class TestCanonicalPlotConfig:
    """Canonical models require typed fitting-mode inputs."""

    def test_plot_config_rejects_legacy_int_mode(self) -> None:
        with pytest.raises(ValidationError):
            PlotConfig.model_validate({"global_fitting": 1})


# ---------------------------------------------------------------------------
# Shared ingress helpers — resolve_column_pair / resolve_context_from_priority
# ---------------------------------------------------------------------------


class TestResolveColumnPair:
    """resolve_column_pair is the canonical column-alias resolver."""

    def test_list_input_returns_string_pair(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair(["energy", "intensity"]) == ("energy", "intensity")

    def test_int_column_is_stringified(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair([0, 1]) == ("0", "1")

    def test_none_returns_defaults(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair(None) == ("energy", "intensity")

    def test_custom_defaults_are_respected(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair(None, default_x="x", default_y="y") == ("x", "y")

    def test_short_list_returns_defaults(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair(["only_one"]) == ("energy", "intensity")

    def test_tuple_input_is_accepted(self) -> None:
        from spectrafit.adapters.unified_config_input import resolve_column_pair

        assert resolve_column_pair(("wavelength", 2)) == ("wavelength", "2")


class TestResolveContextFromPriority:
    """resolve_context_from_priority — context wins over global_."""

    def test_both_none_returns_standard_context(self) -> None:
        from spectrafit.adapters.unified_config_input import (
            resolve_context_from_priority,
        )
        from spectrafit.models.fitting_context import FittingMode

        ctx = resolve_context_from_priority(None, None)
        assert ctx.mode == FittingMode.STANDARD

    def test_global_int_one_returns_global_context(self) -> None:
        from spectrafit.adapters.unified_config_input import (
            resolve_context_from_priority,
        )
        from spectrafit.models.fitting_context import FittingMode

        ctx = resolve_context_from_priority(None, 1)
        assert ctx.mode == FittingMode.GLOBAL

    def test_explicit_context_wins_over_global(self) -> None:
        from spectrafit.adapters.unified_config_input import (
            resolve_context_from_priority,
        )
        from spectrafit.models.fitting_context import FittingContext
        from spectrafit.models.fitting_context import FittingMode

        standard_ctx = FittingContext(mode=FittingMode.STANDARD)
        result = resolve_context_from_priority(standard_ctx, 1)
        assert result.mode == FittingMode.STANDARD

    def test_data_config_args_uses_shared_helper(self) -> None:
        """data_config_from_args_dict honours context > global_ priority."""
        import pathlib

        from spectrafit.adapters.data_config_args import data_config_from_args_dict
        from spectrafit.models.fitting_context import FittingMode

        cfg = data_config_from_args_dict(
            {"infile": pathlib.Path("/tmp/f.txt"), "global_": 1}  # noqa: S108
        )
        assert cfg.context.mode == FittingMode.GLOBAL


class TestStrictUnifiedConfigIngress:
    """Strict config ingress rejects legacy aliases with compatibility guidance."""

    def test_rejects_legacy_global_alias(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"from_legacy_dict\(\).*from_legacy_file\(\)",
        ):
            normalize_strict_unified_config_input({"components": [], "global_": 0})

    def test_rejects_root_infile_alias(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"root-level 'infile' alias",
        ):
            normalize_strict_unified_config_input(
                {"components": [], "infile": "data.csv"}
            )
