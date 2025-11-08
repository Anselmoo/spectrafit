"""Visualize the pkl file as a graph."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Annotated
from typing import Any
from typing import ClassVar

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import typer

from spectrafit.plugins.converter import Converter
from spectrafit.tools import pkl2any
from spectrafit.tools import pure_fname


# Create Typer app
app = typer.Typer(
    help="Converter for 'SpectraFit' from pkl files to a graph.",
    add_completion=False,
)


class PklVisualizer(Converter):
    """Visualize the pkl data as a graph.

    Attributes:
        choices_fformat (ClassVar[set[str]]): The choices for the file format.
        choices_export (ClassVar[set[str]]): The choices for the export format.

    """

    choices_fformat: ClassVar[set[str]] = {"latin1", "utf-8", "utf-16", "utf-32"}
    choices_export: ClassVar[set[str]] = {"png", "pdf", "jpg", "jpeg"}

    @staticmethod
    def convert(infile: Path, file_format: str) -> dict[str, Any]:
        """Convert the input file to the output file.

        Args:
            infile (Path): The input file of the as a path object.
            file_format (str): The encoding of the pickle file.

        Raises:
            TypeError: If the data is not a dictionary.

        Returns:
            Dict[str, Any]: The data as a dictionary, which can be a nested dictionary.

        """
        data = PklVisualizer().get_type(pkl2any(infile, encoding=file_format))
        if not isinstance(data, dict):
            msg = f"Data is not a dictionary: {data}"
            raise TypeError(msg)
        graph = PklVisualizer().create_graph(fname=infile, data_dict=data)

        pos = nx.kamada_kawai_layout(graph, scale=2)
        nx.draw_networkx_nodes(
            graph,
            pos,
            node_size=100,
            node_color="lightblue",
            alpha=0.8,
        )
        nx.draw_networkx_edges(graph, pos, width=0.5, edge_color="grey", alpha=0.5)
        nx.draw_networkx_labels(graph, pos, font_size=10, font_family="sans-serif")
        plt.axis("off")
        return data

    def save(self, data: Any, fname: Path, export_format: str) -> None:
        """Save the graph to a file and the data and their types to a json file.

        Args:
            data (Any): The data to save, which can be a nested dictionary.
            fname (Path): The filename of the file to save.
            export_format (str): The file format to save the graph to.

        Raises:
            ValueError: If the export format is not supported.

        """
        if export_format.lower() not in self.choices_export:
            msg = f"Export format '{export_format}' is not supported."
            raise ValueError(msg)

        plt.savefig(
            pure_fname(fname).with_suffix(f".{export_format}"),
            format=export_format,
        )

        with pure_fname(fname).with_suffix(".json").open("w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_type(self, value: Any) -> dict[str, Any] | str:
        """Get the type of the value.

        Args:
            value (Any): The value to get the type from.

        Returns:
            Union[Dict[str, Any], str]: The type of the value.

        """
        if isinstance(value, dict):
            return {key: self.get_type(value) for key, value in value.items()}
        if isinstance(value, np.ndarray):
            return f"{type(value)} of shape {value.shape}"
        return str(type(value))

    def add_nodes(self, graph: nx.DiGraph, data_dict: dict[str, Any]) -> None:
        """Add nodes to the graph.

        Args:
            graph (nx.DiGraph): The graph to add nodes to.
            data_dict (Dict[str, Any]): The data dictionary to get the nodes from.

        """
        for key, value in data_dict.items():
            graph.add_node(key)
            if isinstance(value, dict):
                for item in value:
                    graph.add_edge(key, item)
                    graph.add_node(item)
                self.add_nodes(graph=graph, data_dict=value)
            elif "of shape" in str(value):
                value = value.split("of shape")
                graph.add_node(value[0])
                graph.add_edge(key, value[0])

                graph.add_node(value[-1])
                graph.add_edge(value[0], value[-1])

            else:
                graph.add_node(value)
                graph.add_edge(key, value)

    def create_graph(self, fname: Path, data_dict: dict[str, Any]) -> nx.DiGraph:
        """Create the graph.

        Args:
            fname (Path): The filename of the file to create the graph from.
            data_dict (Dict[str, Any]): The data dictionary to create the graph from.

        Returns:
            nx.DiGraph: The graph created from the data dictionary.

        """
        graph = nx.DiGraph()
        graph.add_node(str(fname.name))
        for key in data_dict:
            graph.add_edge(str(fname.name), key)

        self.add_nodes(graph=graph, data_dict=data_dict)
        return graph

    def get_args(self) -> dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            dict[str, Any]: Empty dictionary as this converter uses Typer CLI.

        """
        return {}

    def __call__(self) -> None:
        """Call the converter plugin.

        Raises:
            NotImplementedError: This method is not used in the current implementation.
                Use the CLI interface instead.

        """
        msg = "Use the CLI interface (cli_main) instead of calling the converter directly."
        raise NotImplementedError(msg)


@app.command()
def cli_main(
    infile: Annotated[
        Path, typer.Argument(help="Filename of the pkl file to convert to graph.")
    ],
    file_format: Annotated[
        str,
        typer.Option(
            "-f",
            "--file-format",
            help="File format for the optional encoding of the pickle file. Default is 'latin1'.",
        ),
    ] = "latin1",
    export_format: Annotated[
        str,
        typer.Option(
            "-e",
            "--export-format",
            help="File extension for the graph export.",
        ),
    ] = "pdf",
) -> None:
    """Convert pkl files to a visual graph."""
    # Validate choices
    choices_fformat = PklVisualizer.choices_fformat
    choices_export = PklVisualizer.choices_export

    if file_format not in choices_fformat:
        typer.echo(
            f"Error: Invalid file format '{file_format}'. "
            f"Choose from: {', '.join(sorted(choices_fformat))}",
            err=True,
        )
        raise typer.Exit(1)

    if export_format.lower() not in choices_export:
        typer.echo(
            f"Error: Invalid export format '{export_format}'. "
            f"Choose from: {', '.join(sorted(choices_export))}",
            err=True,
        )
        raise typer.Exit(1)

    # Create visualizer instance and run conversion
    visualizer = PklVisualizer()
    try:
        data = visualizer.convert(infile, file_format)
        visualizer.save(data=data, fname=infile, export_format=export_format)
        plt.show()
        typer.echo(f"Successfully visualized {infile}")
    except (TypeError, ValueError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def command_line_runner() -> None:
    """Entry point for the pkl visualizer CLI."""
    app()
