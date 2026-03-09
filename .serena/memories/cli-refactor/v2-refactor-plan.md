# SpectraFit CLI Refactor & Jupyter Core Integration Plan (v2.0.0)

## Summary
7-phase refactor to flatten CLI nesting, move Jupyter to core, add EnvironmentMode, interactive banner, Pydantic fixes in api/, expanded tests, and docs updates.

## User Decisions (confirmed)
- frozen_constraint: full_phase6_unlock — plugins/notebook/ moves to spectrafit/jupyter/
- banner_type: both — Rich startup panel + interactive REPL shell command
- env_detection_scope: full_context_api — EnvironmentMode enum + FittingContext field
- gap_analysis_output: code_fixes_only — apply fixes directly
- backward_compat: remove_plugin — remove `spectrafit plugins jupyter` entirely

## Phase 1: Flatten CLI
Files: NEW spectrafit/cli/commands/jupyter.py, EDIT cli/main.py, cli/commands/plugins/main.py, plugins/discovery.py, pyproject.toml
- Remove "jupyter" from PluginRegistry._builtin_plugins
- Remove [project.entry-points."spectrafit.plugins"] jupyter entry from pyproject.toml
- Keep spectrafit-jupyter script entry point

## Phase 2: New spectrafit/jupyter/ Module
Files: spectrafit/jupyter/{__init__, core, display, plotting, export, solver, launcher}.py
- Copy from spectrafit/plugins/notebook/ with namespace updates
- Replace plugins/notebook/ files with re-export shims for backward compat
- NEVER import from spectrafit.core (use direct module paths to avoid circular import)

## Phase 3: EnvironmentMode + FittingContext
File: spectrafit/models/fitting_context.py
- Add EnvironmentMode(str, Enum): CLI, NOTEBOOK, API
- Add detect_environment() using lazy IPython import
- Add environment: EnvironmentMode = Field(default_factory=detect_environment) to FittingContext

## Phase 4: Interactive Banner
Files: NEW spectrafit/cli/banner.py, NEW spectrafit/cli/commands/shell.py
- banner.py: render_startup_panel(console) — TTY-gated, suppressed in CI/piped mode
- shell.py: `spectrafit shell` interactive REPL with Rich Live fitting loop
- Hook banner into main.py @app.callback()

## Phase 5: Pydantic Gap Fixes (~60 api/ models)
Files: spectrafit/api/{cmd_model, tools_model, models_model, notebook_model, report_model}.py
- Add model_config = ConfigDict(extra="forbid") to all input models
- Keep extra="allow" on result containers in report_model.py (document with # intentional comment)
- DO NOT change SolverAPI (pre-existing Pydantic type mismatch in errorbars field)

## Phase 6: Testing
New: tests/unit/test_cli_jupyter.py, tests/unit/test_banner.py, tests/unit/test_environment_detection.py, tests/integration/test_jupyter_core.py
Update: tests/unit/test_fitting_context.py, tests/integration/test_cli_fit.py

## Phase 7: Documentation
Update: .github/instructions/architecture.instructions.md (add spectrafit/jupyter/, update frozen module table)
Update: CLI help text and epilogs in main.py

## Key Invariants (must not violate)
1. spectrafit/jupyter/ must NOT import from spectrafit.core (circular import risk)
2. extra="forbid" on all input models
3. No sys.exit() in business logic (app.py is the only exception)
4. from __future__ import annotations in every new module
5. All param names via lmfit_param_name()
6. uv run poe ci must be green at each phase commit

## Pydantic Gap Count
61 BaseModel subclasses in api/ missing model_config across:
- cmd_model.py, tools_model.py, models_model.py, notebook_model.py, report_model.py

## Backward Compatibility
- spectrafit plugins jupyter → spectrafit jupyter (removed, top-level only)
- spectrafit-jupyter script: unchanged (kept)
- from spectrafit.plugins.notebook.core import SpectraFitNotebook → re-export shim
- JupyterPlugin entry-point: removed from pyproject.toml

## GitHub Issue
Tracking issue: https://github.com/Anselmoo/spectrafit/issues/2094
