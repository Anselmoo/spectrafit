"""Tests for spectrafit.models.naming — canonical lmfit parameter naming.

Golden-table tests covering all three public functions:
- sanitize_component_id
- lmfit_param_name
- translate_dot_notation
"""

from __future__ import annotations

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.naming import GlobalLmfitContributionKey
from spectrafit.models.naming import dataset_scoped_name
from spectrafit.models.naming import global_contribution_name
from spectrafit.models.naming import global_lmfit_param_name
from spectrafit.models.naming import lmfit_param_name
from spectrafit.models.naming import sanitize_component_id
from spectrafit.models.naming import translate_dot_notation


class TestSanitizeComponentId:
    """sanitize_component_id: ensure lmfit-safe prefix (must start with letter)."""

    @pytest.mark.parametrize(
        ("raw_id", "expected"),
        [
            # Numeric → prefixed with "p"
            ("1", "p1"),
            ("2", "p2"),
            ("39449", "p39449"),
            ("0", "p0"),
            # Alpha → unchanged
            ("main", "main"),
            ("bg", "bg"),
            ("satellite", "satellite"),
            ("main_peak", "main_peak"),
            # Already prefixed
            ("p1", "p1"),
            ("p39449", "p39449"),
            # Mixed: starts with letter → unchanged
            ("m1", "m1"),
            ("left1", "left1"),
        ],
    )
    def test_golden_table(self, raw_id: str, expected: str) -> None:
        assert sanitize_component_id(raw_id) == expected

    def test_idempotent_for_alpha_ids(self) -> None:
        """Calling twice on an alpha id returns the same result."""
        assert sanitize_component_id("main") == sanitize_component_id(
            sanitize_component_id("main")
        )

    def test_idempotent_for_numeric_ids(self) -> None:
        """Calling twice on a numeric id is stable after first sanitization."""
        once = sanitize_component_id("1")  # "p1"
        twice = sanitize_component_id(once)  # "p1" — already starts with letter
        assert once == twice


class TestLmfitParamName:
    """lmfit_param_name: canonical {sanitized_id}_{field_name} formula."""

    @pytest.mark.parametrize(
        ("component_id", "field_name", "expected"),
        [
            # Alpha ids
            ("main", "amplitude", "main_amplitude"),
            ("main", "center", "main_center"),
            ("bg", "slope", "bg_slope"),
            ("bg", "intercept", "bg_intercept"),
            ("satellite", "fwhmg", "satellite_fwhmg"),
            # Numeric ids → sanitized
            ("1", "amplitude", "p1_amplitude"),
            ("1", "center", "p1_center"),
            ("2", "fwhml", "p2_fwhml"),
            ("39449", "sigma", "p39449_sigma"),
            # Already-sanitized numeric ids
            ("p1", "amplitude", "p1_amplitude"),
        ],
    )
    def test_golden_table(
        self, component_id: str, field_name: str, expected: str
    ) -> None:
        assert lmfit_param_name(component_id, field_name) == expected

    def test_sanitization_is_applied(self) -> None:
        """Numeric id must be auto-sanitized."""
        assert lmfit_param_name("1", "amplitude").startswith("p")

    def test_underscore_separator(self) -> None:
        """Separator between id and field is always a single underscore."""
        result = lmfit_param_name("main", "amplitude")
        parts = result.split("_")
        assert len(parts) >= 2


class TestDatasetScopedNames:
    """Global dataset suffix helpers stay owned by canonical naming helpers."""

    @pytest.mark.parametrize(
        ("base_name", "dataset_index", "expected"),
        [
            ("p1_center", 1, "p1_center_1"),
            ("fit", 2, "fit_2"),
            ("residual", "avg", "residual_avg"),
        ],
    )
    def test_dataset_scoped_name(
        self,
        base_name: str,
        dataset_index: int | str,
        expected: str,
    ) -> None:
        assert dataset_scoped_name(base_name, dataset_index) == expected

    def test_global_lmfit_param_name_uses_canonical_base_name(self) -> None:
        assert global_lmfit_param_name("1", "center", 2) == "p1_center_2"

    def test_global_contribution_name_matches_grouped_column_shape(self) -> None:
        assert global_contribution_name("gaussian_main", 3) == "gaussian_main_3"


class TestTranslateDotNotation:
    """translate_dot_notation: user "id.field" → lmfit "id_field"."""

    @pytest.mark.parametrize(
        ("expr", "expected"),
        [
            # Single dot reference
            ("main.amplitude * 0.3", "main_amplitude * 0.3"),
            ("2 * bg.intercept", "2 * bg_intercept"),
            # Multiple dot references
            (
                "left.center + right.center",
                "left_center + right_center",
            ),
            (
                "main.amplitude * satellite.amplitude",
                "main_amplitude * satellite_amplitude",
            ),
            # Already underscore notation — unchanged
            ("main_amplitude * 0.3", "main_amplitude * 0.3"),
            ("plain_name", "plain_name"),
            # No references — unchanged
            ("1.5 * 2.0", "1.5 * 2.0"),  # numeric literals untouched
            ("0.5", "0.5"),
            # Complex expressions
            (
                "(main.amplitude + satellite.amplitude) / 2",
                "(main_amplitude + satellite_amplitude) / 2",
            ),
            # Numeric-prefixed ids (already sanitized)
            ("p1.amplitude + p2.amplitude", "p1_amplitude + p2_amplitude"),
        ],
    )
    def test_golden_table(self, expr: str, expected: str) -> None:
        assert translate_dot_notation(expr) == expected

    def test_numeric_literals_not_translated(self) -> None:
        """Float literals like 3.14 must not be mangled."""
        assert translate_dot_notation("3.14159") == "3.14159"
        assert translate_dot_notation("1.5 * amplitude") == "1.5 * amplitude"

    def test_idempotent(self) -> None:
        """Translating twice gives the same result as translating once."""
        expr = "main.amplitude * 0.3"
        once = translate_dot_notation(expr)
        twice = translate_dot_notation(once)
        assert once == twice


class TestGlobalLmfitContributionKey:
    """Global contribution keys parse from the right-most dataset/field boundary."""

    @pytest.mark.parametrize(
        ("parameter_name", "expected_id", "expected_field", "expected_dataset"),
        [
            ("pseudovoigt_amplitude_1", "pseudovoigt", "amplitude", 1),
            ("gaussian_main_center_2", "gaussian_main", "center", 2),
            ("gaussian_main_fwhmg_12", "gaussian_main", "fwhmg", 12),
        ],
    )
    def test_parse_preserves_full_contribution_id(
        self,
        parameter_name: str,
        expected_id: str,
        expected_field: str,
        expected_dataset: int,
    ) -> None:
        parsed = GlobalLmfitContributionKey.parse(parameter_name)

        assert parsed.contribution_id == expected_id
        assert parsed.field_name == expected_field
        assert parsed.dataset_index == expected_dataset
        assert parsed.contribution_name == f"{expected_id}_{expected_dataset}"

    def test_registry_model_uses_contribution_prefix(self) -> None:
        parsed = GlobalLmfitContributionKey.parse("gaussian_main_amplitude_1")
        assert parsed.registry_model == "gaussian"

    @pytest.mark.parametrize(
        "parameter_name",
        ["missing_dataset", "gaussian__1", "gaussian_main_center_zero"],
    )
    def test_parse_rejects_invalid_names(self, parameter_name: str) -> None:
        with pytest.raises(ValueError):
            GlobalLmfitContributionKey.parse(parameter_name)


class TestV2NamingAuthority:
    """Guardrails for canonical naming behavior in the v2 configuration path."""

    @pytest.mark.unit
    def test_build_composite_model_uses_canonical_lmfit_param_names(self) -> None:
        cfg = UnifiedFittingConfig(
            components=[
                {
                    "id": "1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {
                            "value": 0.0,
                            "vary": False,
                            "expr": "p1.amplitude * 0.5",
                        },
                        "fwhmg": {"value": 0.6, "vary": True},
                    },
                },
                {
                    "id": "bg",
                    "model": "linear",
                    "parameters": {
                        "slope": {"value": 0.0, "vary": True},
                        "intercept": {"value": 1.0, "vary": True},
                    },
                },
            ]
        )

        bundle = cfg.build_composite_model()
        expected_names = {
            lmfit_param_name("1", "amplitude"),
            lmfit_param_name("1", "center"),
            lmfit_param_name("1", "fwhmg"),
            lmfit_param_name("bg", "slope"),
            lmfit_param_name("bg", "intercept"),
        }

        assert expected_names.issubset(set(bundle.params.keys()))
        assert cfg.components[0].parameters["center"].expr == "p1_amplitude * 0.5"
