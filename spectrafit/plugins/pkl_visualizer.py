"""Visualize the pkl file as a graph."""

import argparse
import json

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from spectrafit.plugins.converter import Converter
from spectrafit.tools import pkl2any
from spectrafit.tools import pure_fname


choices_fformat = {"latin1", "utf-8", "utf-16", "utf-32"}
choices_export = {"png", "pdf", "jpg", "jpeg"}


class PklVisualizer(Converter):
    """Visualize the pkl data as a graph."""

    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' from pkl files to a graph."
        )
        parser.add_argument(
            "infile",
            type=Path,
            help="Filename of the pkl file to convert to graph.",
        )
        parser.add_argument(
            "-f",
            "--file-format",
            help="File format for the optional encoding of the pickle file."
            " Default is 'latin1'.",
            type=str,
            default="latin1",
            choices=choices_fformat,
        )
        parser.add_argument(
            "-e",
            "--export-format",
            help="File extension for the graph export.",
            type=str,
            default="pdf",
            choices=choices_export,
        )

        return vars(parser.parse_args())

    @staticmethod
    def convert(infile: Path, file_format: str) -> Dict[str, Any]:
        """Convert the input file to the output file.

        Args:
            infile (Path): The input file of the as a path object.
            file_format (str): The encoding of the pickle file.

        Raises:
            ValueError: If the data is not a dictionary.

        Returns:
            Dict[str, Any]: The data as a dictionary, which can be a nested dictionary.
        """
        data = PklVisualizer().get_type(pkl2any(infile, encoding=file_format))
        if not isinstance(data, dict):
            raise ValueError(f"Data is not a dictionary: {data}")
        graph = PklVisualizer().create_graph(fname=infile, data_dict=data)

        pos = nx.kamada_kawai_layout(graph, scale=2)
        nx.draw_networkx_nodes(
            graph, pos, node_size=100, node_color="lightblue", alpha=0.8
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
        if export_format.lower() not in choices_export:
            raise ValueError(f"Export format '{export_format}' is not supported.")

        plt.savefig(
            pure_fname(fname).with_suffix(f".{export_format}"),
            format=export_format,
        )

        with open(
            pure_fname(fname).with_suffix(".json"), "w+", encoding="utf-8"
        ) as outfile:
            json.dump(data, outfile, indent=4)

    def get_type(self, value: Any) -> Union[Dict[str, Any], str]:
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

    def add_nodes(self, graph: nx.DiGraph, data_dict: Dict[str, Any]) -> None:
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

    def create_graph(self, fname: Path, data_dict: Dict[str, Any]) -> nx.DiGraph:
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

    def __call__(self) -> None:
        """Create the graph and save it as a PDF file."""
        args = self.get_args()
        self.save(
            data=self.convert(args["infile"], args["file_format"]),
            fname=args["infile"],
            export_format=args["export_format"],
        )
        plt.show()


def command_line_runner() -> None:
    """Run the converter from the command line."""
    PklVisualizer()()
