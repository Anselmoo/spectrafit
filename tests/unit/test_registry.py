"""Unit tests for ReferenceKeys model validation (spectrafit.models.model_parameters).

Covers:
- model_check() — accepts all models in DistributionModelAPI
- model_check() — rejects unknown model names
- Confirms automodel_check() and __automodels__ are removed (Phase 1.1 ✅)
"""

from __future__ import annotations

import pytest

from spectrafit.models.model_parameters import ReferenceKeys


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ref() -> ReferenceKeys:
    """Shared ReferenceKeys instance."""
    return ReferenceKeys()


# ---------------------------------------------------------------------------
# model_check
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModelCheck:
    def test_gaussian_accepted(self, ref: ReferenceKeys) -> None:
        ref.model_check("gaussian")  # must not raise

    def test_pseudovoigt_accepted(self, ref: ReferenceKeys) -> None:
        ref.model_check("pseudovoigt")  # must not raise

    def test_lorentzian_accepted(self, ref: ReferenceKeys) -> None:
        ref.model_check("lorentzian")  # must not raise

    def test_voigt_accepted(self, ref: ReferenceKeys) -> None:
        ref.model_check("voigt")  # must not raise

    def test_unknown_model_raises(self, ref: ReferenceKeys) -> None:
        with pytest.raises(NotImplementedError):
            ref.model_check("banana_model")

    def test_model_with_suffix_accepted(self, ref: ReferenceKeys) -> None:
        """Model names with underscore suffix (e.g. gaussian_1) must be valid.

        The check splits on '_' and validates only the prefix.
        """
        ref.model_check("gaussian_1")  # must not raise

    def test_empty_string_raises(self, ref: ReferenceKeys) -> None:
        with pytest.raises(NotImplementedError):
            ref.model_check("")


# ---------------------------------------------------------------------------
# Phase 1.1 regression — automodel_check must be gone
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAutoModelCheckRemoved:
    """Confirm dead auto-detection methods were deleted in Phase 1.1."""

    def test_automodel_check_does_not_exist(self, ref: ReferenceKeys) -> None:
        assert not hasattr(ref, "automodel_check"), (
            "automodel_check() was meant to be deleted in Phase 1.1"
        )

    def test_automodels_attribute_does_not_exist(self, ref: ReferenceKeys) -> None:
        assert not hasattr(ref, "__automodels__"), (
            "__automodels__ was meant to be deleted in Phase 1.1"
        )
