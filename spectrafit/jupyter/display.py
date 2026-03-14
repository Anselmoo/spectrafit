"""DataFrame display utilities for Jupyter notebooks.

This module contains the DataFrameDisplay class for displaying dataframes
in various formats in Jupyter notebooks.
"""

from __future__ import annotations

import importlib

from typing import TYPE_CHECKING

import pandas as pd

from IPython.display import display
from IPython.display import display_markdown


if TYPE_CHECKING:
    from collections.abc import Callable


def _load_optional_display_backend(
    *,
    module_name: str,
    callable_name: str,
    feature_name: str,
) -> Callable[[pd.DataFrame], object]:
    """Load an optional dataframe display backend on demand."""
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        msg = (
            f"{feature_name} display requires optional dependency '{module_name}'. "
            "Install with: pip install spectrafit[jupyter]"
        )
        raise ImportError(msg) from exc

    try:
        backend = getattr(module, callable_name)
    except AttributeError as exc:
        msg = (
            f"{feature_name} display dependency '{module_name}' is missing "
            f"'{callable_name}'. Reinstall with: pip install spectrafit[jupyter]"
        )
        raise ImportError(msg) from exc

    return backend


class DataFrameDisplay:
    """Class for displaying a dataframe in different ways."""

    def df_display(self, df: pd.DataFrame, mode: str | None = None) -> object | None:
        """Call the DataframeDisplay class.

        !!! info "About `df_display`"

            This function is used to display a dataframe in two different ways.

            1. Regular display mode:
                1. Via `IPython.display` for regular sliced displaying of the dataframe
                   in the notebook.
                2. Via `IPython.display` as Markdown for regular displaying of the
                    complete dataframe in the notebook.
            2. Interactive display mode:
                1. Via `itables` for interactive displaying of the dataframe in the
                    notebook, which allows for sorting, filtering, and jumping. For
                    more information see [itables](https://github.com/mwouts/itables).
                2. Via `dtale` for interactive displaying of the dataframe in the
                    notebook, which allows advanced data analysis of the dataframe in
                    an external window. For more information see
                    [dtale](https://github.com/man-group/dtale).

        Args:
            df (pd.DataFrame): Dataframe to display.
            mode (str | None, optional): Display mode. Defaults to None.

        Raises:
            ValueError: Raises ValueError if mode of displaying is not supported.

        Returns:
            Any | None: Returns the dtale object for plotting in the Jupyter
                 notebook, if mode is `dtale`.

        """
        if mode == "regular":
            self.regular_display(df=df)
        elif mode == "markdown":
            self.markdown_display(df=df)
        elif mode == "interactive":
            self.interactive_display(df=df)
        elif mode == "dtale":
            return self.dtale_display(df=df)
        elif mode is not None:
            msg = (
                f"Invalid mode: {mode}. "
                "Valid modes are: regular, interactive, dtale, markdown."
            )
            raise ValueError(
                msg,
            )
        return None

    @staticmethod
    def regular_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a regular way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        """
        display(df)

    @staticmethod
    def interactive_display(df: pd.DataFrame) -> None:
        """Display the dataframe in an interactive way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        """
        itables_show = _load_optional_display_backend(
            module_name="itables",
            callable_name="show",
            feature_name="interactive",
        )
        itables_show(df)

    @staticmethod
    def dtale_display(df: pd.DataFrame) -> object:
        """Display the dataframe in a dtale way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        Returns:
            object: Returns the dtale object for plotting in the Jupyter notebook.

        """
        dtale_show = _load_optional_display_backend(
            module_name="dtale",
            callable_name="show",
            feature_name="dtale",
        )
        return dtale_show(df)

    @staticmethod
    def markdown_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a markdown way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        """
        display_markdown(df.to_markdown(), raw=True)
