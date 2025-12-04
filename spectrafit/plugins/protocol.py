"""Plugin protocol for SpectraFit.

This module defines the plugin interface that all SpectraFit plugins must implement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Protocol
from typing import runtime_checkable


if TYPE_CHECKING:
    import typer


@runtime_checkable
class SpectraFitPlugin(Protocol):
    """Protocol for SpectraFit plugins.

    All plugins must implement this protocol to be discovered and registered
    by the SpectraFit plugin system.

    Example:
        ```python
        class MyPlugin:
            name = "my-plugin"
            version = "1.0.0"
            description = "A sample plugin for SpectraFit"

            def register_commands(self, parent_app: typer.Typer) -> None:
                @parent_app.command(name="myplugin")
                def my_command() -> None:
                    print("Hello from my plugin!")

            def register_models(self) -> list[type]:
                return [MyModel1, MyModel2]
        ```
    """

    name: str
    """Plugin name (unique identifier)."""

    version: str
    """Plugin version following semantic versioning."""

    description: str
    """Short description of the plugin functionality."""

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register CLI commands with the parent Typer app.

        Args:
            parent_app: The parent Typer application to register commands with.

        Example:
            ```python
            def register_commands(self, parent_app: typer.Typer) -> None:
                @parent_app.command(name="mycommand")
                def my_command(arg: str) -> None:
                    print(f"Running with {arg}")
            ```
        """
        ...

    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides.

        Returns:
            List of Pydantic model classes that this plugin provides.

        Example:
            ```python
            def register_models(self) -> list[type]:
                return [MyDataModel, MyConfigModel]
            ```
        """
        ...
