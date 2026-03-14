# Reporting API

!!! note "Canonical reporting surface"

    Runtime reporting ownership lives in `spectrafit.reporting.*`.
    `spectrafit.report` is retained only as a frozen compatibility package for
    legacy imports.

## Active modules

- `spectrafit.reporting.service`
  - `DashboardPayload`
  - `project_dashboard_payload(...)`
  - shared text / markdown / JSON report rendering
- `spectrafit.reporting.dashboard`
  - `write_dashboard_png(...)` for deterministic Matplotlib PNG dashboards

Plotly-backed HTML report behavior remains available through the existing result
and plotting flows; the PNG dashboard path is additive and deterministic rather
than a replacement.

## Canonical usage

```python
from spectrafit.reporting.dashboard import write_dashboard_png
from spectrafit.reporting.service import project_dashboard_payload

payload = project_dashboard_payload(fit_result)
write_dashboard_png(payload, "dashboard.png")
```

::: spectrafit.reporting

## Legacy compatibility

!!! warning "Frozen compatibility package"

    `spectrafit.report` should only be used for historical import compatibility.
    New runtime callers should target `spectrafit.reporting`.

::: spectrafit.report
