"""Unit tests for runtime regression metric extraction."""

from __future__ import annotations

import pandas as pd
import pytest

from spectrafit.core.regression_metrics import (
    RegressionMetrics as CoreRegressionMetrics,
)
from spectrafit.core.regression_metrics import warn_meassage as core_warn_meassage


@pytest.mark.unit
def test_core_regression_metrics_calculates_split_payload() -> None:
    """Runtime regression metrics should still produce split-orient payloads."""
    df = pd.DataFrame(
        {
            "intensity": [1.0, 2.0, 3.0],
            "fit": [1.0, 2.0, 3.0],
        }
    )

    payload = CoreRegressionMetrics(df)()

    assert payload["columns"] == [0]
    assert "r2_score" in payload["index"]
    r2_index = payload["index"].index("r2_score")
    assert payload["data"][r2_index][0] == pytest.approx(1.0)


@pytest.mark.unit
def test_report_metrics_module_re_exports_runtime_metric_implementation() -> None:
    """Legacy report imports should stay compatible via a thin shim."""
    from spectrafit.report.metrics import RegressionMetrics as ReportRegressionMetrics
    from spectrafit.report.metrics import warn_meassage as report_warn_meassage

    assert ReportRegressionMetrics is CoreRegressionMetrics
    assert report_warn_meassage is core_warn_meassage
