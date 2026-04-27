#!/usr/bin/env bash
# Hook: inject-architecture.sh
# Event: SessionStart
# Purpose: Inject the SpectraFit v2 architecture invariants as a system message
#          at the start of every agent session so no context is needed to re-load them.

set -euo pipefail

python3 -c "
import json

SYSTEM_MESSAGE = '''
## SpectraFit v2.0.0 — Architecture Contract (auto-injected)

### Pipeline entry point
CLI / Jupyter / API → UnifiedFittingConfig → FittingPipeline → LmfitSolverRuntime
→ build_composite_bundle() → FitResult → reporting/service.py

### 17 Hard Invariants
1.  lmfit_param_name(id, field) ONLY — no inline f-strings for parameter naming
2.  UnifiedFittingConfig is the SOLE pipeline entry point — no raw dicts across modules
3.  extra=\"forbid\" on ALL input Pydantic models
4.  functools.reduce(operator.add, models) for lmfit model composition — no dict iteration
5.  from __future__ import annotations in EVERY module
6.  No sys.exit() in business logic — raise typed exceptions
7.  translate_dot_notation() at parse time (p1.center → p1_center)
8.  No new from_legacy_dict() usage — prefer model_validate() or from_dict()
9.  PEP 695 type keyword for type aliases (not TypeAlias); StrEnum for string enums
10. Runtime orchestration in spectrafit.core.*, not spectrafit.models.*
11. Jupyter is a core surface — new notebook work in spectrafit.jupyter.*
12. Notebook authoring is typed-first — no new config_payload dict editing flows
13. Reusable workflow logic belongs in spectrafit/, not scripts/
14. Reporting ownership in spectrafit.reporting.* — report/* is frozen compat only
15. No heavyweight generated artifacts committed as source-of-truth UX
16. Shipped notebooks stay aligned with typed notebook contract
17. No repository-layout discovery exposed as public product API

### Module ownership
- spectrafit/core/fitting_config.py   — UnifiedFittingConfig
- spectrafit/core/solver_runtime.py   — LmfitSolverRuntime, SolverExecutionPlan
- spectrafit/models/peak_models.py    — FitParameter, Component
- spectrafit/models/bundle.py         — CompositeModelBundle, build_composite_bundle()
- spectrafit/models/naming.py         — lmfit_param_name() (SINGLE source)
- spectrafit/reporting/service.py     — canonical reporting
- spectrafit/reporting/dashboard.py   — static PNG dashboards (Matplotlib, intentional)

### Migration targets (shrink, do not expand)
- spectrafit/models/solver.py         — delegation wrapper only
- spectrafit/models/parameter_builder.py — move to core/
- spectrafit/models/fitting_request.py   — migrate to UnifiedFittingConfig
- spectrafit/report/*                    — frozen compat, no new code
'''

print(json.dumps({'systemMessage': SYSTEM_MESSAGE.strip(), 'continue': True}))
"
