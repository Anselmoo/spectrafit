"""Shared reporting services for CLI and notebook adapters."""

from __future__ import annotations

from spectrafit.reporting.dashboard import write_dashboard_png
from spectrafit.reporting.service import DashboardPayload
from spectrafit.reporting.service import DashboardTrace
from spectrafit.reporting.service import project_dashboard_payload
from spectrafit.reporting.service import render_json_report
from spectrafit.reporting.service import render_markdown_report
from spectrafit.reporting.service import render_report
from spectrafit.reporting.service import render_text_report


__all__ = [
    "DashboardPayload",
    "DashboardTrace",
    "project_dashboard_payload",
    "render_json_report",
    "render_markdown_report",
    "render_report",
    "render_text_report",
    "write_dashboard_png",
]
