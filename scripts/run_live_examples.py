"""Run example-rooted CLI and notebook live workflows.

This script is a thin wrapper around the reusable workflow runtime and mirrors
the public ``spectrafit examples run`` command.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from spectrafit.workflow.validation import EXAMPLES_DIR
from spectrafit.workflow.validation import EXAMPLE_INPUTS
from spectrafit.workflow.validation import ExampleWorkflowSurface
from spectrafit.workflow.validation import prepare_live_workspace
from spectrafit.workflow.validation import resolved_config
from spectrafit.workflow.validation import run_cli_example
from spectrafit.workflow.validation import run_example_workflows
from spectrafit.workflow.validation import run_notebook_example


if TYPE_CHECKING:
    from pathlib import Path

    from spectrafit.core.fitting_config import UnifiedFittingConfig


# Re-export for backward compatibility with tests
LIVE_OUTPUTS_DIR = "outputs"
LIVE_WORKFLOW_DIR = "live"


# Backward compatibility wrappers (referenced by SLF001 suppressions in old tests)
def _resolved_config(input_toml: Path) -> UnifiedFittingConfig:
    """Backward compatibility wrapper."""
    return resolved_config(input_toml)


# Alias for backward compatibility
_prepare_live_workspace = prepare_live_workspace
_run_cli_example = run_cli_example
_run_notebook_example = run_notebook_example


def main() -> None:
    """Run the complete live CLI and notebook workflows for committed examples."""
    if not EXAMPLE_INPUTS:
        msg = f"No example configs found under '{EXAMPLES_DIR}'."
        raise RuntimeError(msg)

    run_example_workflows(surface=ExampleWorkflowSurface.BOTH, echo=typer.echo)
    typer.echo("[live] All example CLI and notebook workflows completed successfully.")


if __name__ == "__main__":
    main()
