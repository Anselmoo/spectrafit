"""Pytest plugin for collecting and reporting scientific validation results.

This conftest provides fixtures and hooks that collect validation results
during a test session and optionally generate JSON and HTML reports as
CI artifacts using the ``ValidationReport`` model.

Usage:
    Run with ``--validation-report=validation-report`` to produce
    ``validation-report.json`` and ``validation-report.html`` after the session.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from spectrafit.api.validation_model import AnalyticalCheck
from spectrafit.api.validation_model import ExpectationResult
from spectrafit.api.validation_model import ReferenceBenchmark
from spectrafit.api.validation_model import ValidationReport


if TYPE_CHECKING:
    from typing import Protocol

    class RecordValidation(Protocol):
        """Protocol for the ``record_validation`` callable."""

        def __call__(
            self,
            *,
            name: str,
            passed: bool,
            measured: float,
            expected: float,
            tolerance: float,
            category: str,
            metric: str = ...,
            description: str = ...,
        ) -> None:
            """Record a validation result."""
            ...


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--validation-report`` CLI option.

    Args:
        parser: The pytest argument parser.
    """
    parser.addoption(
        "--validation-report",
        action="store",
        default=None,
        metavar="BASENAME",
        help="Base filename for validation report output (e.g. 'validation-report').",
    )


@dataclass
class _ValidationCollector:
    """Internal accumulator for validation results collected during a session.

    Attributes:
        analytical: Analytical ground-truth check results.
        reference: Reference benchmark results.
        expectation: User-defined expectation results.
    """

    analytical: list[AnalyticalCheck] = field(default_factory=list)
    reference: list[ReferenceBenchmark] = field(default_factory=list)
    expectation: list[ExpectationResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Return the total number of collected results."""
        return len(self.analytical) + len(self.reference) + len(self.expectation)

    @property
    def passed(self) -> int:
        """Return the number of passed checks."""
        return (
            sum(c.passed for c in self.analytical)
            + sum(b.passed for b in self.reference)
            + sum(e.passed for e in self.expectation)
        )

    def build_report(self) -> ValidationReport:
        """Construct a ``ValidationReport`` from the collected results.

        Returns:
            A fully populated ``ValidationReport`` instance.
        """
        return ValidationReport(
            timestamp=datetime.now(tz=timezone.utc),
            spectrafit_version=_get_version(),
            analytical_checks=list(self.analytical),
            reference_benchmarks=list(self.reference),
            expectation_results=list(self.expectation),
        )


def _get_version() -> str:
    """Return the installed SpectraFit version string.

    Returns:
        The version string, or ``"unknown"`` if not installed.
    """
    try:
        return _pkg_version("spectrafit")
    except Exception:  # noqa: BLE001
        return "unknown"


# Stash key for sharing the collector between fixtures and hooks.
_collector_key = pytest.StashKey[_ValidationCollector]()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Store an empty collector in the pytest config stash.

    Args:
        config: The pytest configuration object.
    """
    config.stash[_collector_key] = _ValidationCollector()


@pytest.fixture(scope="session")
def validation_collector(request: pytest.FixtureRequest) -> _ValidationCollector:
    """Session-scoped collector that accumulates validation results.

    The collector is shared with the ``pytest_terminal_summary`` hook
    through the config stash.

    Args:
        request: The fixture request (used to access config stash).

    Returns:
        A shared ``_ValidationCollector`` instance for the entire session.
    """
    return request.config.stash[_collector_key]


@pytest.fixture
def record_validation(
    validation_collector: _ValidationCollector,
) -> RecordValidation:
    """Function-scoped fixture that returns a callable for recording results.

    Tests call the returned function to register a validation result into the
    session-scoped collector.

    Args:
        validation_collector: The session-scoped collector fixture.

    Returns:
        A callable that records a single validation result.
    """

    def _record(
        *,
        name: str,
        passed: bool,
        measured: float,
        expected: float,
        tolerance: float,
        category: str,
        metric: str = "rtol",
        description: str = "",
    ) -> None:
        """Record a validation result into the session collector.

        Args:
            name: Identifier for the check.
            passed: Whether the check passed.
            measured: The measured value from the fit.
            expected: The expected ground-truth value.
            tolerance: The tolerance used for comparison.
            category: One of ``"analytical"``, ``"reference"``, or
                ``"expectation"``.
            metric: Comparison metric (default ``"rtol"``).
            description: Optional human-readable description.
        """
        if category == "analytical":
            validation_collector.analytical.append(
                AnalyticalCheck(
                    name=name,
                    passed=passed,
                    expected=expected,
                    measured=measured,
                    tolerance=tolerance,
                    metric=metric,
                    description=description,
                )
            )
        elif category == "reference":
            validation_collector.reference.append(
                ReferenceBenchmark(
                    dataset_name=name,
                    passed=passed,
                    deviation_metric=metric,
                    deviation_value=abs(measured - expected),
                    threshold=tolerance,
                    description=description,
                )
            )
        elif category == "expectation":
            validation_collector.expectation.append(
                ExpectationResult(
                    expectation=name,
                    passed=passed,
                    details=description or f"measured={measured}, expected={expected}",
                )
            )
        else:
            msg = (
                f"Unknown validation category {category!r}. "
                "Use 'analytical', 'reference', or 'expectation'."
            )
            raise ValueError(msg)

    return _record


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """Print a validation summary table and optionally write report files.

    Args:
        terminalreporter: The terminal reporter instance.
        exitstatus: The exit status of the test session.
        config: The pytest configuration object.
    """
    collector: _ValidationCollector | None = config.stash.get(_collector_key, None)
    if collector is None or collector.total == 0:
        return

    terminalreporter.write_sep("=", "Validation Summary")

    _print_category(terminalreporter, "Analytical", collector.analytical)
    _print_category(terminalreporter, "Reference", collector.reference)
    _print_category(terminalreporter, "Expectation", collector.expectation)

    total = collector.total
    passed = collector.passed
    failed = total - passed
    status = "PASSED" if failed == 0 else "FAILED"
    terminalreporter.write_line(f"\nOverall: {status} ({passed}/{total} passed)")

    basename: str | None = config.getoption("--validation-report", default=None)
    if basename is not None:
        report = collector.build_report()
        _write_report_files(basename, report, terminalreporter)


def _print_category(
    terminalreporter: pytest.TerminalReporter,
    label: str,
    items: list[AnalyticalCheck] | list[ReferenceBenchmark] | list[ExpectationResult],
) -> None:
    """Print pass/fail counts for a single validation category.

    Args:
        terminalreporter: The terminal reporter instance.
        label: The category label (e.g. ``"Analytical"``).
        items: The list of validation result items.
    """
    if not items:
        return
    passed = sum(1 for i in items if i.passed)
    failed = len(items) - passed
    terminalreporter.write_line(
        f"  {label:15s}  passed={passed}  failed={failed}  total={len(items)}"
    )


def _write_report_files(
    basename: str,
    report: ValidationReport,
    terminalreporter: pytest.TerminalReporter,
) -> None:
    """Write JSON and HTML report files to disk.

    Args:
        basename: The base filename (without extension).
        report: The validation report to export.
        terminalreporter: The terminal reporter for status messages.
    """
    json_path = Path(f"{basename}.json")
    html_path = Path(f"{basename}.html")

    json_path.write_text(report.to_json(), encoding="utf-8")
    html_path.write_text(report.to_html(), encoding="utf-8")

    terminalreporter.write_line("\nValidation report written to:")
    terminalreporter.write_line(f"  JSON: {json_path}")
    terminalreporter.write_line(f"  HTML: {html_path}")
