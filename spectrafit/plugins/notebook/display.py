"""DataFrame display utilities for Jupyter notebooks.

This module contains the DataFrameDisplay class for displaying dataframes
in various formats in Jupyter notebooks.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from IPython.display import display
from IPython.display import display_markdown
from dtale import show as dtale_show
from itables import show as itables_show


class DataFrameDisplay:
    """Class for displaying a dataframe in different ways."""

    def df_display(self, df: pd.DataFrame, mode: str | None = None) -> Any | None:
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
            mode (str, Optional): Display mode. Defaults to None.

        Raises:
            ValueError: Raises ValueError if mode of displaying is not supported.

        Returns:
            Optional[Any]: Returns the dtale object for plotting in the Jupyter
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
        itables_show(df)

    @staticmethod
    def dtale_display(df: pd.DataFrame) -> Any:
        """Display the dataframe in a dtale way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        Returns:
            Any: Returns the dtale object for plotting in the Jupyter notebook.

        """
        return dtale_show(df)

    @staticmethod
    def markdown_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a markdown way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        """
        display_markdown(df.to_markdown(), raw=True)
